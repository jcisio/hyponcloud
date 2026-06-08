# API Reference

## HyponCloud

Main client class for interacting with the Hypontech Cloud API.

### Methods

#### `__init__(username: str, password: str, session: aiohttp.ClientSession | None = None, timeout: int = 10, retries: int = 3, debug: bool = False, *, oem: int = 0)`

Initialize the client.

- `username`: Your Hypontech Cloud username
- `password`: Your Hypontech Cloud password
- `session`: Optional aiohttp ClientSession. If not provided, one will be created automatically.
- `timeout`: Request timeout in seconds (default: 10)
- `retries`: Number of retry attempts for API requests (default: 3)
- `debug`: Enable debug mode to print HTTP responses with authentication tokens redacted (default: False)
- `oem`: OEM ID to connect to (default: 0)

#### `async connect() -> None`

Authenticate with the API and retrieve access token.

**Raises:**
- `AuthenticationError`: Invalid credentials (HTTP 401)
- `RequestError`: Request failed (network error or server error HTTP 500+)
- `RateLimitError`: Too many requests (HTTP 429)

#### `async get_overview(retries: int | None = None) -> OverviewData`

Get plant overview data including power generation and device status.

**Parameters:**
- `retries`: Number of retry attempts on failure. If None, uses the client's default retry setting

**Returns:** `OverviewData` object

**Raises:**
- `AuthenticationError`: Authentication required
- `RequestError`: Request failed
- `RateLimitError`: Too many requests

#### `async get_list(retries: int | None = None) -> list[PlantData]`

Get list of plants associated with the account.

**Parameters:**
- `retries`: Number of retry attempts on failure. If None, uses the client's default retry setting

**Returns:** List of `PlantData` objects

**Raises:**
- `AuthenticationError`: Authentication required
- `RequestError`: Request failed
- `RateLimitError`: Too many requests

#### `async get_inverters(plant_id: str, retries: int | None = None) -> list[InverterData]`

Get all inverters for a specific plant. This method automatically fetches all pages of inverters.

**Parameters:**
- `plant_id`: The plant ID to get inverters for
- `retries`: Number of retry attempts on failure. If None, uses the client's default retry setting

**Returns:** List of `InverterData` objects

**Raises:**
- `AuthenticationError`: Authentication required
- `RequestError`: Request failed
- `RateLimitError`: Too many requests

#### `async get_batteries(plant_id: str, retries: int | None = None) -> list[BatteryData]`

Get all plant-level batteries for a specific plant. This method automatically fetches all pages of batteries. Inverter responses may also include an embedded battery snapshot.

**Parameters:**
- `plant_id`: The plant ID to get batteries for
- `retries`: Number of retry attempts on failure. If None, uses the client's default retry setting

**Returns:** List of `BatteryData` objects

**Raises:**
- `AuthenticationError`: Authentication required
- `RequestError`: Request failed
- `RateLimitError`: Too many requests

#### `async get_monitor(plant_id: str, retries: int | None = None) -> PlantMonitorData`

Get real-time monitoring data for a specific plant.

**Parameters:**
- `plant_id`: The plant ID to get monitoring data for
- `retries`: Number of retry attempts on failure. If None, uses the client's default retry setting

**Returns:** `PlantMonitorData` object

**Raises:**
- `AuthenticationError`: Authentication required
- `RequestError`: Request failed
- `RateLimitError`: Too many requests

#### `async get_admin_info(retries: int | None = None) -> AdminInfo`

Get administrator account information.

**Parameters:**
- `retries`: Number of retry attempts on failure. If None, uses the client's default retry setting

**Returns:** `AdminInfo` object

**Raises:**
- `AuthenticationError`: Authentication required
- `RequestError`: Request failed
- `RateLimitError`: Too many requests

#### `async close() -> None`

Close the aiohttp session (only if created by the library).

## OverviewData

Data class containing plant overview information.

### Attributes

- `capacity` (float): Plant capacity
- `capacity_company` (str): Capacity unit (e.g., "KW")
- `power` (float): Current power generation in watts
- `company` (str): Power unit (e.g., "W")
- `percent` (int): Percentage value
- `e_today` (float): Today's energy production in kWh
- `e_total` (float): Total lifetime energy production in kWh
- `fault_dev_num` (int): Number of faulty devices
- `normal_dev_num` (int): Number of normal devices
- `offline_dev_num` (int): Number of offline devices
- `wait_dev_num` (int): Number of devices waiting
- `total_co2` (float): Total CO2 savings in tons
- `total_tree` (float): Equivalent trees planted
- `earning` (list[EarningData]): Earnings per currency

## PlantData

Data class containing individual plant information.

### Attributes

- `city` (str): Plant location city
- `company` (str): Power unit (always "W" for `PlantData`, this is added to keep it in sync with `OverviewData`)
- `country` (str): Plant location country
- `e_today` (float): Today's energy production
- `e_total` (float): Total energy production
- `eid` (int): Equipment ID
- `kwhimp` (int): kWh import
- `micro` (int): Micro inverter count
- `plant_id` (str): Unique plant identifier
- `plant_name` (str): Plant name
- `plant_type` (str): Plant type
- `power` (float): Current power
- `status` (str): Plant status
- `time` (str): Last update time
- `photo` (str): Plant photo URL
- `owner_name` (str): Owner username
- `owner_id` (str): Owner account ID
- `top` (int): Top flag
- `property` (int): Property value

## InverterData

Data class containing inverter information.

### Attributes

- `plant_name` (str): Plant name
- `sn` (str): Serial number
- `gateway_sn` (str): Gateway serial number
- `status` (str): Inverter status
- `model` (str): Inverter model
- `software_version` (str): Software version
- `lcd_version` (str): LCD version
- `afci_version` (str): AFCI version
- `afci_version0` (str): AFCI version channel 0
- `afci_version1` (str): AFCI version channel 1
- `afci_version2` (str): AFCI version channel 2
- `time` (str): Last update time
- `spn` (str): SPN identifier
- `power` (float): Current power output in watts
- `eid` (str): Equipment ID
- `device_type` (str): Device type
- `fault` (int): Fault status
- `plant_id` (str): Plant ID
- `modbus` (int): Modbus status
- `e_total` (float): Total energy production in kWh
- `e_today` (float): Today's energy production in kWh
- `property` (int): Property value
- `nick_name` (str): Nickname
- `com` (int): Communication status
- `system_connect_mode` (int): System connection mode
- `third_active_power` (int): Third party active power
- `third_meter_energy` (int): Third party meter energy
- `today_generation_third` (int): Today's generation from third party
- `warning` (int): Warning status
- `gateway` (GatewayData | None): Gateway device info
- `battery` (BatteryData | None): Optional embedded battery snapshot from the inverter endpoint; use `get_batteries()` for the full plant-level battery list
- `port` (list[PortData]): Port configurations

## BatteryData

Data class containing battery information from the plant battery endpoint or an embedded inverter battery snapshot.

### Attributes

- `time` (str): Last update time
- `sn` (str): Battery serial number
- `status` (str): Battery status, when included in inverter responses
- `soc` (float): Battery state of charge percentage
- `ahrtg` (float): Rated amp-hours, when included in inverter responses
- `wh` (float): Battery energy capacity in watt-hours, when included in inverter responses
- `ohk` (int): `OHK` value from the battery endpoint
- `a_bat` (float): Battery current
- `a_bat_inv` (float): Inverter-side battery current
- `achamax` (float): Maximum charge current
- `adischamax` (float): Maximum discharge current
- `battery_model` (str): Battery model code
- `gateway_model` (str): Gateway model
- `gsn` (str): Gateway serial number
- `gsn_version` (str): Gateway software version
- `huayu` (int): Huayu flag/value
- `inv_sn` (str): Inverter serial number
- `manufacturer` (str): Battery manufacturer
- `model` (str): Battery model name
- `mosstate` (int): MOS state
- `ncyc` (int): Cycle count
- `pid` (str): Plant ID
- `plant_name` (str): Plant name
- `single_hp_bat_sns` (list[str] | None): Single high-power battery serial numbers, if reported
- `spn` (str): SPN identifier
- `st` (int): Battery state code
- `software_version` (str): Battery software version
- `upgrade_state` (int): Upgrade state code
- `v_bat` (float): Battery voltage
- `v_bat_inv` (float): Inverter-side battery voltage

## PlantMonitorData

Data class containing real-time monitoring data for a specific plant.

### Attributes

- `monetary` (str): Currency code (e.g., "EUR")
- `today_earning` (float): Today's earnings
- `month_earning` (float): This month's earnings
- `total_earning` (float): Total lifetime earnings
- `e_today` (float): Today's energy production in kWh
- `e_month` (float): This month's energy production in kWh
- `e_year` (float): This year's energy production in kWh
- `e_total` (float): Total lifetime energy production in kWh
- `total_tree` (float): Equivalent trees planted
- `total_co2` (float): Total CO2 savings in kg
- `total_diesel` (float): Equivalent diesel saved in litres
- `percent` (float): Performance percentage
- `meter_power` (float): Grid power in watts
- `power_load` (float): Load power in watts
- `w_cha` (float): Charging power in watts
- `power_pv` (float): PV power in watts
- `soc` (float): Battery state of charge percentage
- `micro` (int): Micro inverter flag
- `warning` (str): Warning status

## EarningData

Data class containing earnings information per currency.

### Attributes

- `currency` (str): Currency code (e.g., "EUR")
- `today` (float): Today's earnings
- `total` (float): Total earnings

## GatewayData

Data class containing gateway device information.

### Attributes

- `sn` (str): Serial number
- `model` (str): Gateway model
- `status` (str): Gateway status
- `time` (str): Last update time
- `push_time` (int): Push interval in seconds
- `pid` (str): PID

## PortData

Data class containing inverter port information.

### Attributes

- `sn` (str): Serial number
- `id` (str): Port ID
- `x` (int): X coordinate
- `y` (int): Y coordinate
- `port` (int): Port number

## AdminInfo

Data class containing administrator account information.

### Attributes

- `parent_name` (str): Parent account name
- `parent_id` (str): Parent account ID
- `role` (list[str] | None): User roles
- `has_lower_level` (bool): Whether account has lower level access
- `id` (str): User ID
- `eid` (int): Equipment ID
- `username` (str): Username
- `login_name` (str): Login name
- `email` (str): User email address
- `first_name` (str): First name
- `last_name` (str): Last name
- `company` (str): Company name
- `country` (str): Country
- `city` (str): City
- `address` (str): Address line 1
- `address2` (str): Address line 2
- `postal_code` (str): Postal code
- `mobile` (str): Mobile phone number
- `mobile_prefix_code` (str): Mobile country prefix code
- `city_mobile_code` (str): City mobile code
- `country_mobile_code` (str): Country mobile code
- `language` (str): Language preference
- `currency` (str): Currency preference
- `timezone` (str): Timezone
- `photo` (str): Profile photo URL
- `last_login_time` (str): Last login timestamp
- `last_login_ip` (str): Last login IP address
- `created_at` (str): Account creation timestamp
- `deleted_at` (str): Account deletion timestamp
- `manufacturer` (int): Manufacturer flag
- `switch_warning` (int): Switch warning flag
- `is_internal` (int): Internal account flag
- `status` (int): Account status
- `first_login` (bool): Whether this is the first login
- `token` (str): Session token

## Exceptions

- `HyponCloudError`: Base exception for all library errors
- `AuthenticationError`: Authentication failed (invalid credentials)
- `RequestError`: API request failed
- `RateLimitError`: API rate limit exceeded
