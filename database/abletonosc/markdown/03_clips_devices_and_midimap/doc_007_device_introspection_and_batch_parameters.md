# Device Introspection & Batch Parameter Control

> **Module:** `abletonosc.device`  
> **Upstream Handlers:** `DeviceHandler`  
> **Key Capabilities:** Parameter arrays, batch mutations, real-time value listeners  

---

## 1. Device Metadata Reflection

Devices are addressed by `(track_index, device_index)`:

- Get device class name: `/live/device/get/class_name <track> <device>` -> `"Eq8"`, `"Compressor2"`, `"Drift"`.
- Get device display name: `/live/device/get/name <track> <device>` -> `"EQ Eight"`.
- Get device type: `/live/device/get/type <track> <device>` -> `0` = audio effect, `1` = instrument, `2` = midi effect.
- Number of parameters: `/live/device/get/num_parameters <track> <device>`.

---

## 2. Bulk Parameter Array Queries

Instead of querying 50 parameters one-by-one, AbletonOSC provides bulk property arrays:

| Endpoint | Parameters | Return Value |
| :--- | :--- | :--- |
| `/live/device/get/parameters/name` | `track, device` | Tuple of all parameter name strings. |
| `/live/device/get/parameters/value` | `track, device` | Tuple of all current parameter float values. |
| `/live/device/get/parameters/min` | `track, device` | Tuple of all parameter minimum float values. |
| `/live/device/get/parameters/max` | `track, device` | Tuple of all parameter maximum float values. |
| `/live/device/get/parameters/is_quantized` | `track, device` | Tuple of bools indicating discrete vs continuous. |

### Fast Parameter Map Ingestion:
```python
def get_device_parameter_map(client, track: int, device: int) -> dict:
    names = client.query("/live/device/get/parameters/name", (track, device))
    values = client.query("/live/device/get/parameters/value", (track, device))
    mins = client.query("/live/device/get/parameters/min", (track, device))
    maxs = client.query("/live/device/get/parameters/max", (track, device))
    
    # Skip track/device prefix in return tuple:
    names, values, mins, maxs = names[2:], values[2:], mins[2:], maxs[2:]
    
    return {
        name: {"value": val, "min": mi, "max": ma}
        for name, val, mi, ma in zip(names, values, mins, maxs)
    }
```

---

## 3. Batch Parameter Setting (`/live/device/set/parameters/value`)

AbletonOSC allows setting multiple parameters in an atomic call:
```text
/live/device/set/parameters/value <track> <device> <val_0> <val_1> <val_2> ...
```

For individual parameter updates:
```text
/live/device/set/parameter/value <track> <device> <param_index> <float_val>
```

---

## 4. Real-Time Parameter Listeners

AbletonOSC allows attaching listeners to parameter knobs to track manual user movements:
- Start listening: `/live/device/start_listen/parameter/value <track> <device> <param_index>`
- Incoming event: `/live/device/get/parameter/value <track> <device> <param_index> <current_val>`
- Stop listening: `/live/device/stop_listen/parameter/value <track> <device> <param_index>`
