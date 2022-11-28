import os
import re

from tqdm import tqdm

in_folder = r""
out_folder = r""

if __name__ == '__main__':
	files = os.listdir(in_folder)

	for f in tqdm(list(filter(lambda x: "part1" in x, files))):
		pattern = re.compile(f.replace("part1", r"part\d"))
		in_files = [os.path.join(in_folder, f) for f in files if pattern.match(f)]
		out_file = f.replace(" - part1", "")

		tempf = 'tempfile'
		s = ''
		for f in in_files:
			s += f"file '{f}'\n"
		open(tempf, 'w').write(s)
		cmd = f'ffmpeg -f concat -safe 0 -i {tempf} -c copy "{os.path.join(out_folder, out_file)}"'
		os.system(cmd)