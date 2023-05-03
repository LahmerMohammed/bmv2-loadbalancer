/* -*- P4_16 -*- */
#include <core.p4>
#include <v1model.p4>


const bit<16> TYPE_IPV4 = 0x800;

typedef bit<9>  egressSpec_t;
typedef bit<48> macAddr_t;
typedef bit<32> ipv4Addr_t;


#define CPU_PORT 510
#define DROP_PORT 511


header ethernet_t {// packet_out and packet_in are named here from the perspective of the
    macAddr_t dstAddr;
    macAddr_t srcAddr;
    bit<16>   etherType;
}

header ipv4_t {
    bit<4>    version;
    bit<4>    ihl;
    bit<6>    dscp;
    bit<2>    ecn;
    bit<16>   totalLen;
    bit<16>   identification;
    bit<3>    flags;
    bit<13>   fragOffset;
    bit<8>    ttl;
    bit<8>    protocol;
    bit<16>   hdrChecksum;
    ipv4Addr_t srcAddr;
    ipv4Addr_t dstAddr;
}

header tcp_t{
    bit<16> srcPort;
    bit<16> dstPort;
    bit<32> seqNo;
    bit<32> ackNo;
    bit<4>  dataOffset;
    bit<4>  res;
    bit<8>  flags;
    bit<16> window;
    bit<16> checksum;
    bit<16> urgentPtr;
}

header udp_t {
    bit<16> srcPort;
    bit<16> dstPort;
    bit<16> length_;
    bit<16> checksum;
}

struct metadata {
    bit<32> ecmp_path_id;

    // Currently this will only be equal to L4 destination port
    bit<16> ecmp_group_id;


    bit<16> l4Length;
}

// Note on the names of the controller_header header types:

// packet_out and packet_in are named here from the perspective of the
// controller, and that is how these messages are named in the
// P4Runtime API specification as well.

// Thus packet_out is a packet sent out of the controller to the
// switch, which becomes a packet received by the switch on port
// CPU_PORT.

// A packet sent by the switch to port CPU_PORT becomes a PacketIn
// message to the controller.

// When running with simple_switch_grpc, you must provide the
// following command line option to enable the ability for the
// software switch to receive and send such messages:
//
//     --cpu-port 510
//     --drop-port 511


enum bit<7> Reason_t {
    NO_RULE_MATCH   = 14
}

@controller_header("packet_in")
header packet_in_header_t {
    bit<9> ingress_port;
    Reason_t reason;
}

@controller_header("packet_out")
header packet_out_header_t {
    bit<9> egress_port;
    bit<7> padding_bits;
}


struct headers {
    packet_in_header_t  packet_in;
    packet_out_header_t packet_out;
    ethernet_t   ethernet;
    ipv4_t       ipv4;
    tcp_t        tcp;
    udp_t        udp;
}


parser MyParser(packet_in packet,
                out headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {

    

    state start {
        transition parse_ethernet;
    }
    state parse_ethernet {
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.etherType) {
            0x800: parse_ipv4;
            default: accept;
        }
    }
    state parse_ipv4 {
        packet.extract(hdr.ipv4);

        meta.l4Length = hdr.ipv4.totalLen - (bit<16>)hdr.ipv4.ihl * 4;
        
        transition select(hdr.ipv4.protocol) {
            6: parse_tcp;
        }
    }
    state parse_tcp {
        packet.extract(hdr.tcp);
        transition accept;
    }
}


/*************************************************************************
************   C H E C K S U M    V E R I F I C A T I O N   *************
*************************************************************************/

control MyVerifyChecksum(inout headers hdr, inout metadata meta) {
    apply {  }
}

/*************************************************************************
**************  I N G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {
    action drop() {
        mark_to_drop(standard_metadata);
    }

    action no_action() {}

    action snat_a(ipv4Addr_t dstIpAddr, macAddr_t dstMacAddr,
                  ipv4Addr_t srcIpAddr,bit<16> srcPort, bit<9> egress_port) {
        hdr.ethernet.dstAddr = dstMacAddr; 

        hdr.tcp.srcPort = srcPort;

        hdr.ipv4.srcAddr = srcIpAddr;
        hdr.ipv4.dstAddr = dstIpAddr;
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;

        standard_metadata.egress_spec = egress_port;
    }

    action reverse_snat_a(ipv4Addr_t dstIpAddr, bit<16> dstPort, // user ip and port
                          macAddr_t dstMacAddr, ipv4Addr_t srcIpAddr, bit<9> egress_port) {

        hdr.ethernet.dstAddr = dstMacAddr;

        hdr.ipv4.dstAddr = dstIpAddr;
        hdr.ipv4.srcAddr = srcIpAddr;
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;

        hdr.tcp.dstPort = dstPort;

        standard_metadata.egress_spec = egress_port;
    }

    action send_to_controller() {
        standard_metadata.egress_spec = CPU_PORT;
        hdr.packet_in.setValid();
        hdr.packet_in.reason = Reason_t.NO_RULE_MATCH;
        hdr.packet_in.ingress_port = standard_metadata.ingress_port;
    }

    table service {
        key = {
            hdr.tcp.dstPort: exact;
        }

        actions = {
            no_action;
            drop;
        }
        size = 1024;
        default_action = drop;
    }

    table snat_t {
        key = {
            hdr.ipv4.srcAddr: exact;
            hdr.tcp.srcPort: exact;
            hdr.tcp.dstPort: exact;
        }
        actions = {
            snat_a;
            send_to_controller;
        }
        default_action = send_to_controller;
        size = 1024;
    }

    table reverse_snat_t {
        key = {
            hdr.tcp.dstPort: exact;
        }
        actions = {
            reverse_snat_a;
            drop;
        }
        default_action = drop;
        size = 1024;
    }

    apply {

        if (hdr.ipv4.isValid() && hdr.ipv4.ttl > 0 && hdr.tcp.isValid()) {

            if (standard_metadata.ingress_port == 0) {
                switch(service.apply().action_run) {
                    no_action: {
                        snat_t.apply();
                    }
                    
                    // If 'no_action' action haven't been executed, means 'send_to_controller' action 
                    // have been executed as it is the default action, therefore we should terminate 
                    // the processing of this packet as it was sent to the controller
                }           
                
            } 
            else {
                reverse_snat_t.apply();  
            }
        }

    }
}

/*************************************************************************
****************  E G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyEgress(inout headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata) {
 
    action rewrite_mac(macAddr_t smac) {
        hdr.ethernet.srcAddr = smac;
    }

    table send_frame {
        key = {
            standard_metadata.egress_spec: exact;
        }
        actions = {
            rewrite_mac;
        }
    }

    apply {
        send_frame.apply();
    }
}

/*************************************************************************
*************   C H E C K S U M    C O M P U T A T I O N   **************
*************************************************************************/

control MyComputeChecksum(inout headers hdr, inout metadata meta) {
     apply {
	    update_checksum(
	    hdr.ipv4.isValid(),
            { hdr.ipv4.version,
	          hdr.ipv4.ihl,
              hdr.ipv4.dscp,
              hdr.ipv4.ecn,
              hdr.ipv4.totalLen,
              hdr.ipv4.identification,
              hdr.ipv4.flags,
              hdr.ipv4.fragOffset,
              hdr.ipv4.ttl,
              hdr.ipv4.protocol,
              hdr.ipv4.srcAddr,
              hdr.ipv4.dstAddr },
              hdr.ipv4.hdrChecksum,
              HashAlgorithm.csum16);

        update_checksum_with_payload(
            hdr.tcp.isValid(),
            { 
              hdr.ipv4.srcAddr,
              hdr.ipv4.dstAddr,
              8w0,
              hdr.ipv4.protocol,
              meta.l4Length,
              hdr.tcp.srcPort,
              hdr.tcp.dstPort,
              hdr.tcp.seqNo,
              hdr.tcp.ackNo,
              hdr.tcp.dataOffset,
              hdr.tcp.res,
              hdr.tcp.flags,
              hdr.tcp.window,
              hdr.tcp.urgentPtr
            },
            hdr.tcp.checksum,
            HashAlgorithm.csum16);

        update_checksum_with_payload(hdr.udp.isValid(),
            { 
                hdr.ipv4.srcAddr,
                hdr.ipv4.dstAddr,
                8w0,
                hdr.ipv4.protocol,
                meta.l4Length,
                hdr.udp.srcPort,
                hdr.udp.dstPort,
                hdr.udp.length_
            },
            hdr.udp.checksum, HashAlgorithm.csum16);
    }
}

/*************************************************************************
***********************  D E P A R S E R  *******************************
*************************************************************************/

control MyDeparser(packet_out packet, in headers hdr) {
    apply {

        packet.emit(hdr.packet_in);
        
        //parsed headers have to be added again into the packet.
        packet.emit(hdr.ethernet);
        packet.emit(hdr.ipv4);

        //Only emited if valid
        packet.emit(hdr.tcp);
        packet.emit(hdr.udp);
    }
}

/*************************************************************************
***********************  S W I T C H  *******************************
*************************************************************************/

//switch architecture
V1Switch(
MyParser(),
MyVerifyChecksum(),
MyIngress(),
MyEgress(),
MyComputeChecksum(),
MyDeparser()
) main;
