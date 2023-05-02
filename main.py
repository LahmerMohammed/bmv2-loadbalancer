from controller import Controller
from config import BMV2_SWITCH

p4i_file_path=BMV2_SWITCH['p4i_file_path']
bmv2_json_file_path=BMV2_SWITCH['json_file_path']


def main():
    controller = Controller(p4i_file_path, bmv2_json_file_path)

    try:
        controller.receivePacketsFromDataplane()
    except KeyboardInterrupt:
            print("[!] Shutting down.")
    
    controller.shutdown()




if __name__ == '__main__':
#   run(p4i_file_path=BMV2_SWITCH['p4i_file_path'],bmv2_json_file_path=BMV2_SWITCH['json_file_path'])
    main()
