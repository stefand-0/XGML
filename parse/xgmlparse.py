# Copyright 2026 Stefan
#
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import sys
import re
import math

class XGMLTranspiler:
    def __init__(self):
        self.variables = {}
        self.gcode = ["G28", "G90", "G1 Z0.2 F3000"]
        self.feed_rate = "F3000"
        self.z_offset = 0.0

    def resolve_val(self, token):
        if token in self.variables:
            return float(self.variables[token])
        try:
            return float(token)
        except ValueError:
            return 0.0

    def add_circle(self, radius, segments=32):
        for i in range(segments + 1):
            angle = 2 * math.pi * i / segments
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            self.gcode.append(f"G1 X{x:.2f} Y{y:.2f} {self.feed_rate}")

    def add_square(self, size):
        coords = [(0,0), (size,0), (size,size), (0,size), (0,0)]
        for x, y in coords:
            self.gcode.append(f"G1 X{x:.2f} Y{y:.2f} {self.feed_rate}")

    def process_block(self, lines):
        idx = 0
        while idx < len(lines):
            line = lines[idx].strip()
            
            if line.startswith(';') or line.startswith('#'):
                idx += 1
                continue
                
            line = re.sub(r'', '', line).strip()
            
            if not line or line.startswith('<module') or line == 'end>':
                idx += 1
                continue

            if line.startswith('<var'):
                match = re.search(r'(\w+):\s*([\w.]+)', line)
                if match:
                    self.variables[match.group(1)] = match.group(2)
                idx += 1
                continue

            if line.startswith('<temperature'):
                nozzle_match = re.search(r'nozzle:([\w.]+)', line)
                bed_match = re.search(r'bed:([\w.]+)', line)
                if nozzle_match:
                    noz_val = self.resolve_val(nozzle_match.group(1))
                    self.gcode.append(f"M104 S{noz_val:.0f}")
                if bed_match:
                    bed_val = self.resolve_val(bed_match.group(1))
                    self.gcode.append(f"M140 S{bed_val:.0f}")
                idx += 1
                continue

            if line.startswith('<fan'):
                speed_match = re.search(r'speed:([\w.]+)', line)
                if speed_match:
                    speed_val = self.resolve_val(speed_match.group(1))
                    self.gcode.append(f"M106 S{speed_val:.0f}")
                idx += 1
                continue

            if '@f' in line:
                match = re.search(r'@f(\d+)', line)
                if match:
                    self.feed_rate = f"F{match.group(1)}"

            if line.startswith('<loop'):
                for_match = re.search(r'@for\s+([\w.]+)', line)
                zstep_match = re.search(r'@zstep\s+([\w.]+)', line)
                iterations = 1
                if for_match:
                    iterations = int(self.resolve_val(for_match.group(1)))
                z_step_val = 0.0
                if zstep_match:
                    z_step_val = self.resolve_val(zstep_match.group(1))
                
                loop_lines = []
                idx += 1
                depth = 1
                while idx < len(lines):
                    sub_line = lines[idx].strip()
                    if sub_line.startswith('<loop'):
                        depth += 1
                    elif sub_line == 'end>':
                        depth -= 1
                        if depth == 0:
                            break
                    loop_lines.append(lines[idx])
                    idx += 1
                
                for _ in range(iterations):
                    if z_step_val > 0:
                        self.gcode.append(f"G1 Z{self.z_offset:.2f} {self.feed_rate}")
                    self.process_block(loop_lines)
                    self.z_offset += z_step_val
                idx += 1
                continue

            if '@PREDEF CIRCLE' in line:
                match = re.search(r'r:([\w.]+)', line)
                if match:
                    r = self.resolve_val(match.group(1))
                    self.add_circle(r)
                idx += 1
                continue

            if '@PREDEF SQUARE' in line:
                match = re.search(r'size:([\w.]+)', line)
                if match:
                    s = self.resolve_val(match.group(1))
                    self.add_square(s)
                idx += 1
                continue

            if '<path' in line or '<polygon' in line or '@' in line:
                coords = re.findall(r'([xyze]):([\w.]+)', line)
                if coords:
                    parts = []
                    for axis, val_token in coords:
                        val = self.resolve_val(val_token)
                        if axis.lower() == 'z':
                            val += self.z_offset
                        if axis.lower() == 'e':
                            parts.append(f"E{val:.4f}")
                        else:
                            parts.append(f"{axis.upper()}{val:.2f}")
                    cmd = "G1 " + " ".join(parts)
                    self.gcode.append(f"{cmd} {self.feed_rate}")

            idx += 1

    def transpile(self, input_file): #confusing? this gave me alot of errors
        if not (input_file.endswith('.xgml') or input_file.endswith('.xgm')):
            print("ERR: File must have .xgml or .xgm extension")
            return
        
        if input_file.endswith('.xgml'):
            output_file = input_file.replace('.xgml', '.gcode')
        else:
            output_file = input_file.replace('.xgm', '.gcode')

        try:
            with open(input_file, 'r') as f:
                lines = f.readlines()
        except FileNotFoundError:
            print(f"ERR: File {input_file} not found.")
            return

        self.process_block(lines)

        with open(output_file, 'w') as f:
            f.write("\n".join(self.gcode))
        print(f"Success: {output_file} generated.")

def main():
    if len(sys.argv) > 1:
        transpiler = XGMLTranspiler()
        transpiler.transpile(sys.argv[1])
    else:
        print("Usage: xgml <filename.xgml>")

if __name__ == "__main__":
    main()
# don't comment your code, its better this way :)))