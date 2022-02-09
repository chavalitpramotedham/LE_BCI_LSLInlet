from pylsl import StreamInlet, resolve_byprop
from time import time

def record(
        duration: int,
        dejitter=False,
        continuous: bool = True,
) -> None:
    # constants:
    LSL_EEG_CHUNK = 1
    LSL_SCAN_TIMEOUT = 5
    LSL_BUFFER = 360

    # initialization
    chunk_length = LSL_EEG_CHUNK

    print("Looking for stream...")
    # CHANGE NAME TO BCI STREAM
    # streams = resolve_byprop('name', 'Unity.LEBCI_Stream', timeout=LSL_SCAN_TIMEOUT)
    streams = resolve_byprop('name', 'BrainVision RDA', timeout=LSL_SCAN_TIMEOUT)

    if len(streams) == 0:
        print("Can't find stream.")
        return

    print("Started acquiring data.")
    inlet = StreamInlet(streams[0], max_chunklen=chunk_length)
    # eeg_time_correction = inlet.time_correction()

    print("Looking for a Markers stream...")
    marker_streams = resolve_byprop(
        'name', 'Unity.LEBCI_Stream', timeout=LSL_SCAN_TIMEOUT)

    if marker_streams:
        inlet_marker = StreamInlet(marker_streams[0])
        print("Found Markers stream")
    else:
        inlet_marker = False
        print("Can't find Markers stream.")
        return

    info = inlet.info()
    description = info.desc()

    Nchan = info.channel_count()

    ch = description.child('channels').first_child()
    ch_names = [ch.child_value('label')]
    for i in range(1, Nchan):
        ch = ch.next_sibling()
        ch_names.append(ch.child_value('label'))

    res = []
    timestamps = []
    markers = []

    currentSample = []
    inBCI = False

    t_init = time()
    time_correction = inlet.time_correction()
    last_written_timestamp = None

    print('Start recording at time t=%.3f' % t_init)
    print('Time correction: ', time_correction)
    while (time() - t_init) < duration:
        try:

            # 1. Check for data and append to res & timestamp arrays

            data, timestamp_d = inlet.pull_chunk(
                timeout=1.0, max_samples=chunk_length)

            # #debug
            # if (data):
            #     print("DATA: "+str(data))
            # if (timestamp_d):
            #     print("DATA TIMESTAMP: "+str(timestamp_d))

            if timestamp_d:
                res.append(data)
                timestamps.extend(timestamp_d)
                tr = time()

                if (inBCI):
                    currentSample.append((data,timestamp_d))

            # 2. Check for markers and append to markers array

            if inlet_marker:
                marker, timestamp_m = inlet_marker.pull_sample(timeout=0.0)

                # #debug
                # if (marker):
                #     print("MARKER: "+str(marker))
                # if (timestamp_m):
                #     print("MARKER TIMESTAMP: "+str(timestamp_m))

                if timestamp_m:
                    markers.append([marker, timestamp_m])

                    if int(marker[0]) == 102:
                        print("BCI START")
                        currentSample = []
                        inBCI = True

                    elif int(marker[0]) == 101 and inBCI:
                        print("BCI END")
                        inBCI = False
                        print(currentSample)

            # # Save every 5s
            # if continuous and (last_written_timestamp is None or last_written_timestamp + 5 < timestamps[-1]):
            #     _save(
            #         filename,
            #         res,
            #         timestamps,
            #         time_correction,
            #         dejitter,
            #         inlet_marker,
            #         markers,
            #         ch_names,
            #         last_written_timestamp=last_written_timestamp,
            #     )
            #     last_written_timestamp = timestamps[-1]

        except KeyboardInterrupt:
            break

    time_correction = inlet.time_correction()
    print("Time correction: ", time_correction)

    # _save(
    #     filename,
    #     res,
    #     timestamps,
    #     time_correction,
    #     dejitter,
    #     inlet_marker,
    #     markers,
    #     ch_names,
    # )
    #
    # print("Done - wrote file: {}".format(filename))


if __name__ == "__main__":
    record(100)