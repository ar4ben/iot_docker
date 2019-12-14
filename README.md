# Quick setup CO2/Humidity/Temperature monitoring system with grafana dashboard on Raspberry Pi (DHT22 and MH-Z19 sensors)

![Alt](./img/Dashboard.png "Dashboard")

- Connect DHT22 sensor:
  ![Alt](./img/DHT22.jpeg "DHT22")
  [Instruction](https://pimylifeup.com/ "Instruction")
- Connect MH-Z19 sensor:
  ![Alt](./img/MHZ19.jpg "MHZ19")
  [Instruction](https://monitorserviceatelierueda.blogspot.com/2018/11/how-to-measure-room-co2-concentration.html "Instruction")
- For reading from MH-Z19:

  * Add the line "enable_uart=1" to the '/boot/config.txt' file
  * Remove the phrase "console=serial0,115200" from the '/boot/cmdline.txt' file
  * Reboot Pi.

- Install Docker:

  `curl -sSL https://get.docker.com | sh`

  `sudo usermod -aG docker $USER`

  reboot or logout

- Install Docker-compose:
  `pip3 install docker-compose`

- Clone this repo and run:

  `docker-compose up`

- When everything is running go to http://localhost:3000/ and use login/pass: admin/admin. Choose "iot" dashboard.
