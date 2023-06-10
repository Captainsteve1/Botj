import subprocess
import os
import uuid
import shutil

def get_muxed_file(
    dir: str,
) -> str:
    try:
        return sorted([
            {"file": os.path.join(root, name), "size": int(os.path.getsize(os.path.join(root, name)))}
            for root, dirs, files in os.walk(dir)
            for name in files
        ], key=lambda k: k["size"])[-1]["file"]
    except IndexError:
        return None

def tmp_folder() -> str:
    return str(uuid.uuid1()).replace("-", "")

def mp4demuxer(
	mp4demuxerexe: str,
	infile: str,
	outfile: str,
) -> None:
	tmp = tmp_folder()
	os.makedirs(tmp, exist_ok=True)
	cmd = [mp4demuxerexe, "--input-file", infile, "--output-folder", tmp]
	code = subprocess.call(cmd)
	if not code == 0:
		raise SystemError("%s exit with status code %d" % (mp4demuxerexe, code))

	out = get_muxed_file(tmp)
	shutil.move(out, outfile)
	shutil.rmtree(tmp)
	return
