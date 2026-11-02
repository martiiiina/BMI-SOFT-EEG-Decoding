import pyxdf
import itertools

path = "data/bids/2026-10-28/sub-P015/ses-S002/eeg/sub-P015_ses-S002_task-Default_run-001_eeg.xdf"

"""An XDF file holds several independent streams of data, each with its own header and footer. 
The streams are stored in a list, and the file-level header is returned separately. 
Each stream has a time series of samples and corresponding timestamps."""
streams, file_header = pyxdf.load_xdf(path)   # list of streams + file-level header
print(f"File header: {file_header}")
print(f"Number of streams: {len(streams)}")
print(f"Stream headers: {[s['info']['name'][0] for s in streams]}")   # stream names

s = streams[0]
print(f"Stream info: {s['info'].keys()}")
print(f"Time series shape: {s['time_series'].shape}")
print(f"Time stamps shape: {s['time_stamps'].shape}")
print(f"Stream footer: {s['footer'].keys()}")

# Channels description: type, unit, label
chans = s['info']["desc"][0]["channels"][0]["channel"]
for (ctype, unit), run in itertools.groupby(
        enumerate(chans), key=lambda p: (p[1]["type"][0], p[1]["unit"][0] if p[1]["unit"] else "-")):
    run = list(run)
    first, last = run[0], run[-1]
    print(f"  columns {first[0] + 1:>3}-{last[0] + 1:<3} | {len(run):>3} x {ctype:<8} | unit: {unit:<3} "
          f"| {first[1]['label'][0]} .. {last[1]['label'][0]}")

print(f"Number of channels: {s['info']['channel_count'][0]}")
print(f"Nominal sampling rate: {s['info']['nominal_srate'][0]}")
print(f"duration_s: {len(s['time_series']) / float(s['info']['nominal_srate'][0])}")
