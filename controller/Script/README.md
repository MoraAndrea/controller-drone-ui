To install RabbitMQ it use the following command: 

    # apt install rabbitmq-server
    
### Rabbit Federation

To use Federation, RabbitMQ Broker must be configured with a User, Policy and Federation Upstreams.

First of all install Federation Plugin:

    $ sudo /usr/sbin/rabbitmq-plugins enable rabbitmq_federation rabbitmq_federation_management

then restart RabbitMQ.

In order to setup the federation between the different RabbitMQ servers, you can:
* Follow the manual installation described in [README_RABBITMQ.md]() 
* Run the script [script/rabbit_setup.py]() as superuser:

        $ sudo python3 -m script.rabbit_setup

The script create a new user, a Policy and all Federation Upstreams.

To decide with which broker to federate, the peers list must be modified in the script.
For example, on rabbit0 Broker, federate to 1 and 2 the list will be:

    peers = [["rabbit1", "10.0.0.1"],["rabbit2","10.0.0.2"]]

Where "rabbit1" is the name of federation upstream towards the rabbit1 Broker.

You can modify the [config/config.ini]() file with the chosen credentials and federation parameters.

### Run

Make sure rabbitmq is running:

    # service rabbitmq-server start
