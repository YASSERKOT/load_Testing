import asyncio
import json
import threading

import requests as r
import time
from datetime import datetime

import websockets


class Device:
    def __init__(self, lane):
        self.lane = lane

    def activate_io(self, io, f=None):
        response = r.get(f"http://{self.lane['ip']}:{self.lane['port']}/io.setIO?name={io}&active=true").json()
        if f is not None:
            f.write(f"{datetime.now()} ## Lane.activate_io ##{io} is set to TRUE.\n")
        return response

    def deactivate_io(self, io, f=None):
        response = r.get(f"http://{self.lane['ip']}:{self.lane['port']}/io.setIO?name={io}&active=false").json()
        if f is not None:
            f.write(f"{datetime.now()} ## Lane.activate_io ##{io} is set to FALSE.\n")
        return response


class Lane(Device):
    def __init__(self, lane):
        super().__init__(lane)

    def get_infos(self, f=None, print_log=True):
        infos = r.get(f"http://{self.lane['ip']}:{self.lane['port']}/vtp.getInfo").json()
        if f is not None and print_log:
            f.write(f"{str(datetime.now())} ## Hopper::get_infos ## {infos}\n")
        return infos

    def is_closed(self, f=None):
        return self.get_infos(f, False)['mode'] == 'closed'

    def presence_loop_is_activated(self, f=None):
        return self.get_infos(f, False)['state'] != 'waitingVehicle'

    def open_lane(self, f=None):
        if f is not None:
            f.write(f"{datetime.now()} ## Lane::open_lane() ##---> Opening lane\n")
        r.get(
            f"http://{self.lane['ip']}:{self.lane['port']}/vtp.setMode_Automatic?maintenance=false&operatorId={self.lane['user_id']}")
        if self.get_infos(f, False)['state'] == 'waitingVehicle':
            if f is not None:
                f.write(f"{str(datetime.now())} ## Lane::open_lane ## Lane opened successfully.\n")
            return True
        if f is not None:
            f.write(f"{str(datetime.now())} ## Lane::open_lane ## Failed opening the lane.\n")
        return False

    def simulate_bill(self, type, f=None):
        if f is not None:
            f.write(f"{datetime.now()} ## Lane::simulate_bill() ##---> Simulating bill of {type / 100}\n")
        response = r.get(f"http://{self.lane['ip']}:{self.lane['port']}/mop_bill_vl.simulate_Bill?value={type}").json()
        return response

    def simulate_vehicle_presence(self, f=None):
        if f is not None:
            f.write(f"{datetime.now()} ## Lane::simulate_vehicle_presence() ##---> Simulating vehicle presence.\n")
        return self.activate_io('IN_LOOP_PRESENT', f)

    def simulate_vehicle_leave(self, f=None):
        if f is not None:
            f.write(f"{datetime.now()} ## Lane::simulate_vehicle_leave() ##---> Simulating vehicle presence.\n")
        # Activate the leaving loop
        self.activate_io('IN_LOOP_LEAVE', f)
        # Deactivating the leaving loop
        response = self.deactivate_io('IN_LOOP_LEAVE', f)
        return response


class Hopper(Device):
    def __init__(self, lane):
        super().__init__(lane)
        # Initialize the content of the VAULT
        self.coins_details = {}
        self.coins_total_count = 0
        self.update_hopper_content()
        self.result_available = threading.Event()
        self.payment_details = {}

    def get_infos(self, f=None, print_log=True):
        infos = r.get(f"http://{self.lane['ip']}:{self.lane['port']}/hopper.getInfo").json()
        if f is not None and print_log:
            f.write(f"{str(datetime.now())} ## Hopper::get_infos ## {infos}")
        return infos

    def on_failure(self, f=None):
        return self.get_infos(f, False)["status"] == "Failure"

    def update_hopper_content(self, f=None):
        if f is not None:
            f.write(f"{datetime.now()} ## Hopper::update_hopper_content() ##---> Updating the content of the hopper\n")
        infos = self.get_infos(f, False)['actual']['CoinHopper']
        old_content = dict()
        old_content['coins_details'] = self.coins_details
        old_content['coins_total_count'] = self.coins_total_count
        self.coins_details = infos['details']
        self.coins_total_count = infos['actual']
        # Return the old content
        return old_content

    def give_money(self, amount, f=None):
        if f is not None:
            f.write(f"{datetime.now()} ## Hopper::give_money() ##---> Giving an amount of {amount}\n")
        status_dict = r.get(f"http://{self.lane['ip']}:{self.lane['port']}/hopper.getStatus").json()
        result = False
        if status_dict['response'] != 'OutOfOrder':
            f.write(f"{datetime.now()} ## Hopper::give_money() ##---> Sending an amount of {amount}\n")
            response = r.get(
                f"http://{self.lane['ip']}:{self.lane['port']}/hopper.giveMoney?amountInCents=#{amount}").json()
            # Update the hopper content informations
            self.update_hopper_content(f)
            f.write(response['response'])
            if response['response'] == amount:
                result = True
        f.write(f"{datetime.now()} ## Hopper::give_money() ##---> Amount was ejected successfully ? {result}\n")
        return result

    def add_coins(self, count, type, f=None):
        f.write(
            f"{datetime.now()} ## Hopper::add_coins() ##---> Adding {count} coins of {type} in the vault of the smart"
            f"hopper\n")
        f.write(f"{datetime.now()} ## Hopper::add_coins() ##---> Old coins details : {self.coins_details}\n")
        r.get(
            f"http://{self.lane['ip']}:{self.lane['port']}/hopper.addCoins?countOfCoins={count}&denominationInCents={type}")
        # Update the hopper content informations
        self.update_hopper_content(f)
        result = False
        infos = self.get_infos(f, False)['actual']['CoinHopper']
        if infos['actual'] == self.coins_total_count:
            self.coins_details = infos['details']
            f.write(f"{datetime.now()} ## Hopper::add_coins() ##---> New coins details : {infos['details']}\n")
            result = True
        f.write(f"{datetime.now()} ## Hopper::add_coins() ##---> Coins were added successfully ? {result}\n")

    # async def getHopperEvent(self):
        # uri = "ws://172.31.94.132:8091/SmartHopper/hopper"
        # async with websockets.connect(uri) as websocket:
            # events = await websocket.recv()
            # print(f"{events}")

    async def get_cashDistributed(self, uri, lane, data_dict, key, f=None, timeout=60):
        self.payment_details = []
        timeout = time.time() + timeout
        async with websockets.connect(uri) as websocket:
            # Simulate a bill payment.
            lane.simulate_bill(data_dict[key]['payment_bill'], f)
            print(f"Opening websocket {uri}")
            async for event in websocket:
                print("Iterating through the WebSocket events")
                # event = json.loads( await websocket.recv() )
                event = json.loads(event)
                if event['__source'] == "SmartHopper/hopper":
                    print("SmartHopper event detected")
                    if str.upper(event['__type']) == str.upper('MoneyDistributorDevice_MoneyAmountEvent'):
                        print("MoneyDistributorDevice_MoneyAmountEvent detected")
                        # we will use the hopper of index 0 as we are testing with only one hopper
                        # TODO : Generalize to multiple hoppers
                        if event['paymentList'][0]['accepted']['coins'] != '':
                            f.write(
                                f"{datetime.now()} ## Hopper::get_cashDistributed() ##---> Ejected pieces {event['paymentList'][0]['accepted']['coins']}.\n")
                            self.payment_details = str.split(event['paymentList'][0]['accepted']['coins'])
                            print(self.payment_details)
                            break
                else:
                    print("Not SmartHopper event detected !!")
                if time.time() > timeout :
                    break
            return self.payment_details

    def get_ejected_coins(self, lane, data_dict, key, f=None, timeout=60):
        old_content = self.update_hopper_content(f)
        # Get the given amount details
        print('Accessing the event listener routine')
        asyncio.get_event_loop().run_until_complete(self.get_cashDistributed("ws://172.31.94.132:8091/hopper", lane, data_dict, key, f))
        print('Accessing the event listener routine')
        each_coin_count = dict()
        for coin in set(self.payment_details):
            each_coin_count[coin] = self.payment_details.count(coin)
        f.write(
            f"{datetime.now()} ## Hopper::get_ejected_coins() ##---> Ejected {json.dumps(self.payment_details)}.\n")
        return each_coin_count

    def empty_hopper_vault(self, f=None, timeout=60):
        res = False
        if f is not None:
            f.write(f"{datetime.now()} ## Hopper::empty_hopper_vault() ##---> Emptying the hopper vault from its "
                    f"content.\n")
        self.deactivate_io('IN_COINS_VAULT_PRESENT', f)
        self.activate_io('IN_COINS_VAULT_PRESENT', f)
        timeout = time.time() + timeout
        while True:
            infos = self.get_infos(f, False)['actual']
            if 'actual' in infos['CoinVault']:
                if infos['CoinVault']['actual'] == '0':
                    res = True
                break
            f.write(
                f"{datetime.now()} ## Hopper::empty_hopper_vault() ##---> Waiting the simulation of vault change.")
            if time.time() > timeout:
                f.write(f"{datetime.now()} ## Hopper::empty_hopper_vault() ##---> Timeout elapsed!! Test Failed \n")
                break
        f.write(f"{datetime.now()} ## Hopper::empty_smart_hopper() ##---> Emptying succeeded ? {res}\n")
        return res

    def empty_smart_hopper(self, f=None):
        res = False
        if f is not None:
            f.write(f"{datetime.now()} ## Hopper::empty_smart_hopper() ##---> Emptying the hopper from its content.\n")
            f.write(
                f"{datetime.now()} ## Hopper::empty_smart_hopper() ##---> Content before emptying {self.get_infos(f)}.\n")

        self.coins_details = {}
        self.coins_total_count = 0
        r.get(f"http://{self.lane['ip']}:{self.lane['port']}/hopper.emptyHopper")
        # Wait until the hopper is emptying itself.
        time.sleep(75)
        if self.get_infos(f, False)['actual']['CoinHopper']['actual'] == '0':
            res = True
        f.write(f"{datetime.now()} ## Hopper::empty_smart_hopper() ##---> Emptying succeeded ? {res}\n")
        return res


class Elevator(Device):
    def __init__(self, lane):
        super().__init__(lane)
        self.coins_nb = 0
        self.coins_details = {
            "100": 0,
            "200": 0,
            "10": 0,
            "20": 0,
            "50": 0
        }

    def get_infos(self, f=None, print_log=True):
        infos = r.get(f"http://{self.lane['ip']}:{self.lane['port']}/elevator.getInfo").json()
        if f is not None and print_log:
            f.write(f"{str(datetime.now())} ## Elevator::get_infos ## {infos}\n")
        return infos

    def is_ready(self, f=None):
        current_state = self.get_infos(f, True)['state']
        if f is not None:
            f.write(f"{str(datetime.now())} ## Elevator::is_ready ? {current_state == 'Idle'} ## {current_state}\n")
        return current_state == 'Idle'

    def is_mounting_coins(self, f=None):
        current_state = self.get_infos(f, False)['state']
        if f is not None:
            f.write(f"{str(datetime.now())} ## Elevator::is_ready ? {current_state == 'Emptying'} ## {current_state}\n")
        return current_state == 'Emptying'

    def fill_Hopper_signal(self, f=None):
        if f is not None:
            f.write(f"{str(datetime.now())} ## Elevator::fill_hopper_signal ## Sending coins up\n")
        status_dict = r.get(f"http://{self.lane['ip']}:{self.lane['port']}/elevator.getStatus").json()
        if status_dict['response'] != 'Error':
            response = r.get(f"http://{self.lane['ip']}:{self.lane['port']}/elevator.sigEmptyHopper")
            return True
        return False

    def cancel_payout(self, f=None):
        if f is not None:
            f.write(f"{str(datetime.now())} ## Elevator::cancelPayout ## Canceling the refill operation\n")
        r.get(f"http://{self.lane['ip']}:{self.lane['port']}/elevator.sigCancelPayout")
        return True

    def wait_lastPayoutCalculation(self, f=None, timeout=60):
        if f is not None:
            f.write(f"{str(datetime.now())} ## Elevator::wait_lastPayoutCalculation\n")
        timeout = time.time() + timeout
        while True:
            if self.is_ready(f) and 'lastPayout' in self.get_infos(f, True):
                break
            f.write(f"{datetime.now()} ## Elevator::wait_lastPayoutCalculation() ##---> Waiting for elevator to be "
                    f"Idle.\n")
            if time.time() > timeout:
                f.write(f"{datetime.now()} ## Elevator::wait_lastPayoutCalculation() ##---> Timeout elapsed!! Test Failed \n")
                break

    def get_last_payout(self, f=None, timeout=60):
        lastPayout = 0
        if f is not None:
            f.write(f"{str(datetime.now())} ## Elevator::get_last_payout\n")
        # This signal will update the last payout info
        r.get(f"http://{self.lane['ip']}:{self.lane['port']}/elevator.sigLastPayout")
        timeout = time.time() + timeout
        while True:
            if self.is_ready(f):
                break
            f.write(
                f"{str(datetime.now())} ## Elevator::get_last_payout ## Waiting to change the state of the elevator "
                f"to 'Idle'\n")
            if time.time() > timeout:
                f.write(f"{datetime.now()} ## Elevator::get_last_payout() ##---> Timeout elapsed!! Test Failed \n")
                lastPayout = False
                break
        lastPayout = self.get_infos(f, True)['lastPayout']
        if f is not None:
            f.write(
                f"{str(datetime.now())} ## Elevator::get_last_payout ## Last payout is {self.get_infos(f, True)['lastPayout']}\n")
        return lastPayout

    def set_elevator_container_details(self, coins_details, f=None):
        if f is not None:
            f.write(f"{str(datetime.now())} ## Elevator::set_elevator_container_details ## Setting coins details in "
                    f"the elevator "
                    f"container\n")
            f.write(
                f"{str(datetime.now())} ## Elevator::set_elevator_container_details ## Old coins details {self.coins_details}\n")
            f.write(
                f"{str(datetime.now())} ## Elevator::set_elevator_container_details ## Old coins number {self.coins_nb}\n")
        for k in self.coins_details:
            # Add the number of coins depending on the type of coins returned back by the hopper.
            if k in coins_details:
                self.coins_details[k] += int(coins_details[k])
                self.coins_nb += int(coins_details[k])
        f.write(
            f"{str(datetime.now())} ## Elevator::set_elevator_container_details ## New coins details {self.coins_details}\n")
        f.write(
            f"{str(datetime.now())} ## Elevator::set_elevator_container_details ## New coins number {self.coins_nb}\n")
        if f is not None:
            f.write(f"{str(datetime.now())} ## Elevator::set_elevator_container_details ## Elevator coins container "
                    f"contains {self.coins_details}\n")
        return self.coins_details

    def reset_coins_nb(self):
        self.coins_nb = 0

    def get_elevator_container_details(self, f=None):
        if f is not None:
            f.write(f"{str(datetime.now())} ## Elevator::get_elevator_container_details ## Getting elevator container "
                    f"details\n")
        return self.coins_nb, self.coins_details

    def hopper_is_empty(self, initial_content, f=None):
        res = True
        for coin in initial_content:
            if int(initial_content[coin]) != int(self.coins_details[coin]):
                res = False
        if f is not None:
            f.write(f"{str(datetime.now())} ## Elevator::hopper_is_empty ## Hopper is empty ? {res}\n")
        return res

    def hopper_almost_empty(self, minimal_amount, initial_content, f=None):
        res = False
        sum = 0
        for coin in initial_content:
            if coin in self.coins_details:
                sum += int(coin) * (int(initial_content[coin]) - int(self.coins_details[coin]))
        f.write(
            f"{str(datetime.now())} ## Elevator::hopper_almost_empty ## Remaining amount in hopper is : {sum}cents\n")
        if sum < int(minimal_amount):
            res = True
        if f is not None:
            f.write(f"{str(datetime.now())} ## Elevator::hopper_almost_empty ## Hopper is almost empty ? {res}\n")
        return res


class Eagle(Device):
    def __init__(self, lane):
        super().__init__(lane)

    def get_infos(self, f=None, print_log=True):
        infos = r.get(f"http://{self.lane['ip']}:{self.lane['port']}/eagle.getInfo").json()
        if f is not None and print_log:
            f.write(f"{str(datetime.now())} ## Eagle::get_infos ## {infos}\n")
        return infos
