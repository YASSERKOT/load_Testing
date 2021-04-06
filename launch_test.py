######################################
##### Stress Testing the devices #####
## Written in 11/03/2020 (Y.KOTRSI) ##
######################################
import json
import requests as r
import time
import os
from datetime import datetime
from utils import Hopper, Elevator, Lane

with open('test_config.json', 'r') as config_data:
    data_dict = json.load(config_data)
    for key in data_dict:
        # Load the configuration of each test
        TEST_CONFIG = data_dict[key]

        if key == "lane":
            lane_dic = data_dict[key]
            lane = Lane(lane_dic)
            hopper = Hopper(lane_dic)
            elevator = Elevator(lane_dic)
        else:
            print("*********************************************************")
            print("Warning :: Make sure that the coins are in Smart Hopper !!")
            input(f"INFO :: Click any keyboard key to launch the {key}.\n\n\n")
            print("*********************************************************")
            print("*********************************************************")

            # Tests are to be written here !!
            # First Test.
            timestr = time.strftime("%Y%m%d-%H%M%S")
            with open(os.path.join('output', f"{timestr}_Test_log.log" ), 'w') as report_file:
                # Simulate the emptying of the hopper vault.
                hopper.empty_hopper_vault(report_file)

                report_file.write(f"{str(datetime.now())} ################### ####################\n")
                report_file.write(f"{str(datetime.now())} ## MAIN::{key} ## BEGINNING OF TEST\n")
                report_file.write(
                    f"{str(datetime.now())} ## MAIN::{key} ## Charge steps : {data_dict[key]['charge_steps']}\n")
                report_file.write(
                    f"{str(datetime.now())} ## MAIN::{key} ## Iteration timeout : {data_dict[key]['timeout']}\n")
                report_file.write(
                    f"{str(datetime.now())} ## MAIN::{key} ## Used payment bill : {data_dict[key]['payment_bill']}\n")
                for coin in data_dict[key]['coins']:
                    report_file.write(
                        f"{str(datetime.now())} ## MAIN::{key} ## Number of coin {coin} CENTS : {data_dict[key]['coins'][coin]}\n")
                report_file.write(f"{str(datetime.now())}              ###########                 \n")

                # Fill the initial content dictionary with the initial content of the Hopper:
                initial_content = dict()
                initial_nb_coins = 0
                for coin in data_dict[key]['coins']:
                    initial_content[coin] = data_dict[key]['coins'][coin]
                    initial_nb_coins += int(data_dict[key]['coins'][coin])
                    # Initializing the content of the hopper with the content fixed in the config file.
                    hopper.add_coins(data_dict[key]['coins'][coin], coin, report_file)
                # A variable to sum up the number of the coins ejected each time.
                global_coin_number = 0
                # Open Lane.
                if lane.is_closed():
                    lane.open_lane(report_file)
                    print("Lane opened")
                    time.sleep(10)
                # LAUNCH THE TEST.
                for iteration in range(int(data_dict[key]['charge_steps'])):
                    report_file.write(f"{str(datetime.now())} ## MAIN::{key} ## ITERATION NB : {iteration + 1}\n")
                    print(" - - - - - - - - - -")
                    print(f"{key} :: Iteration NUM : {iteration+1}")
                    # Simulate a vehicle presence on the presence loop if it isn't already activated.
                    if not lane.presence_loop_is_activated():
                        lane.simulate_vehicle_presence(report_file)
                        print("Simulate vehicle presence")
                    print(f"Simulate bill of {data_dict[key]['payment_bill']}")
                    # Get the change amount details.
                    print("Getting ejected coins for this operation")
                    coins = hopper.get_ejected_coins(lane, data_dict, key, report_file, timeout=data_dict[key]["timeout"])
                    print("Ejected coins in this operation : ")
                    print(coins)
                    # Get the content of the elevator coins container.
                    elevator.set_elevator_container_details(coins, report_file)
                    nb_coins, coins_details = elevator.get_elevator_container_details(report_file)

                    print("Number of coins in the elevator container : " + str(nb_coins))
                    print("Details of coins in the elevator container : ")
                    print(coins_details)
                    # Simulate a vehicle leaving on the exit loop.
                    lane.simulate_vehicle_leave(report_file)
                    print("Simulate vehicle leave")
                    time.sleep(2)
                    # Check if the hopper content is inferior than the minimal amount of money fixed.
                    # if iteration != 0 and elevator.hopper_almost_empty(int(data_dict[key]['min_amount']), initial_content, report_file):
                    #     # If the hopper is almost empty send a signal to the elevator to refill it.
                    #     elevator.fill_Hopper_signal(report_file)
                    #     time.sleep(12)
                    #     elevator.cancel_payout(report_file)
                    #     for coin in coins_details:
                    #         hopper.add_coins(coins_details[coin], coin, report_file)

                    # Check if the hopper is almost empty
                    if iteration != 0 and elevator.hopper_almost_empty(int(data_dict[key]['min_amount']), initial_content, report_file):
                        # If the hopper is empty send a signal to the elevator to refill it.
                        elevator.fill_Hopper_signal(report_file)
                        print("Sending a starting elevator signal")
                        # Wait for the elevator to refill the hopper
                        # TODO : Change the timeout dynamically to the test case in the configuration file.
                        time.sleep(data_dict[key]['giving_back_coins'])
                        # Cancel the refill after the timeout set of delivering the coins.
                        elevator.cancel_payout(report_file)
                        print("Stopping the elevator")
                        # Wait the elevator to calculate the lastPayout.
                        elevator.wait_lastPayoutCalculation(report_file)

                        print("Coins counted by the elevator sensor : " + elevator.get_last_payout(report_file))
                        print(" Coins ejected by the Smart Hopper : " + str(nb_coins))
                        print(" Ejecting operation number : " + str(global_coin_number))

                        if int(elevator.get_last_payout(report_file)) == nb_coins:
                            print("Adding coins to the hopper")
                            for coin in coins_details:
                                hopper.add_coins(coins_details[coin], coin, report_file)
                                elevator.coins_details[coin] = 0
                                global_coin_number += nb_coins
                            elevator.reset_coins_nb()
                            nb_coins = 0

                            report_file.write(
                                f"{str(datetime.now())} ## MAIN::FIRST TEST ## Coins successfully sent back to the "
                                f"hopper\n")
                            time.sleep(1)
                            # Check if the hopper is on failure after refilling it, if yes loop on it.
                            while hopper.on_failure(report_file):
                                report_file.write(
                                    f"{str(datetime.now())} ## MAIN::FIRST TEST ## FAILURE : Smart Hopper is on Failure"
                                    f" !!\n")
                        else:
                            report_file.write(
                                f"{str(datetime.now())} ## MAIN::FIRST TEST ## FAILURE : Mismatch in coins number, "
                                f"iteration failed.. ending test !!\n")
                            break
                    report_file.write(
                        f"{str(datetime.now())} ## MAIN::{key} ## ENDING OF {iteration + 1} ITERATION\n")
                    report_file.write(f"{str(datetime.now())} ################### ####################\n")
                # End of the test.
                # Initialize the hopper content.
                #hopper.empty_smart_hopper(report_file)