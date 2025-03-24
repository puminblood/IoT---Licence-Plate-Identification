from gps3 import gps3

def get_gps_location(timeout=5):
    gps_socket=gps3.GPSDSocket()
    data_stream = gps3.DataStream()
    gps_socket.connect()
    gps_socket.watch()

    for _ in range(timeout * 2):
        try:
            new_data = next(gps_socket)
            if new_data:
                data_stream.unpack(new_data)
                lat = data_stream.TPV.get("lat")
                lon = data_stream.TPV.get("lon")
                if lat and lon:
                    return round(lat, 6), round(lon, 6)
        except StopIteration:
            break
        except Exception:
            continue
    
    return None, None