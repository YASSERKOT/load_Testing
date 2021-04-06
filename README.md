# load_Testing
<br/>
Load Testing framework for coin recycling devices chain (Coins Hopper elevator + Hopper )
<br/>
<br/>

# Description
<br/>
This framework contains functionality to manage a load testing operation on two embeded automation that were implemented to operate over two devices (Hopper coin recycler and the Hopper elevator). The software make calls for some remote comands (REST API) to simulate  payment operations in a configured load to raise the bar for the two automations in order to calculate their respective performances (The API that was developed to forward the calls for the embedded automation is not included in this source code). 

<br/>
<br/>

# Configuration
<br/>
To configure a test case, an external configuration file was set up for this purpose: <br/>

``` Json File
{
	"lane": { 
		"ip": "",     # Set up the ip for the server to which the program will send the Rest call to simulate actions and on which the event observers will listen. 
		"port": "",   # The port used on the server to externalise its API.
    "user_id": "" # A user id used to identify on the lane management software on which the API is integrated.
	},
	"TEST_02": {    # The test case name. 
		"charge_steps": , # The number of the payment iterations 
		"timeout": ,      # A timeout to break the load testing whenever the system doesn't respond.
		"payment_bill": , # A simulation for the used payment bill.
		"giving_back_coins":, # The amount that should be returned back by the recycler.
		"coins" : { # This part configure the number of the physical coins used in this test. 
			"100": ,
			"200": ,
			"10": ,
			"20": ,
			"50": 
		},
		"min_amount": # A value that will be controlled by the test to check if the devices chain failed in counting and recycling the coins.
	}
}
```

<br/>
<br/>

# Refrences
<br/>
Coins Hopper elevator device : https://www.aseuro.co.uk/products/fh-700l1/ <br/>
Smart hopper : https://viewpro.eu/shop/vending-en/smart-hopper-coin-recycler/
