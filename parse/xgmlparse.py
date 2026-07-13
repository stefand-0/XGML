import sys
import re
import math


class XGMLTranspiler:
    def __init__(self):
        self.variables = {}
        self.gcode = []
        self.feed_rate = "F3000"
        self.z_offset = 0.0
        self.cumulative_e = 0.0
        self.extrusion_rate = 0.05
        self.last_x = 0.0
        self.last_y = 0.0
        self.last_z = 0.0

    def resolve_val(self, token):
        if token in self.variables:
            return float(self.variables[token])
        try:
            return float(token)
        except ValueError:
            raise ValueError(f"Unknown variable or literal: '{token}'")

    def strip_comments(self, line):
        line = re.sub(r'#.*', '', line)
        line = re.sub(r';.*', '', line)
        return line.strip()

    def add_circle(self, radius):
        segments = max(64, int(2 * math.pi * radius / 0.5))
        circumference = 2 * math.pi * radius
        e_per_segment = (circumference / segments) * self.extrusion_rate

        x0 = radius
        y0 = 0.0
        self.gcode.append(f"G0 X{x0:.2f} Y{y0:.2f} {self.feed_rate}")
        self.last_x = x0
        self.last_y = y0

        for i in range(1, segments + 1):
            angle = 2 * math.pi * i / segments
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            self.cumulative_e += e_per_segment
            self.gcode.append(
                f"G1 X{x:.2f} Y{y:.2f} E{self.cumulative_e:.4f} {self.feed_rate}"
            )
            self.last_x = x
            self.last_y = y

    def add_square(self, size):
        coords = [(0, 0), (size, 0), (size, size), (0, size), (0, 0)]

        self.gcode.append(f"G0 X{coords[0][0]:.2f} Y{coords[0][1]:.2f} {self.feed_rate}")
        self.last_x = coords[0][0]
        self.last_y = coords[0][1]

        for i in range(1, len(coords)):
            x, y = coords[i]
            dist = math.hypot(x - self.last_x, y - self.last_y)
            self.cumulative_e += dist * self.extrusion_rate
            self.gcode.append(
                f"G1 X{x:.2f} Y{y:.2f} E{self.cumulative_e:.4f} {self.feed_rate}"
            )
            self.last_x = x
            self.last_y = y

    def emit_move(self, coords_dict):
        parts = []
        has_extrusion = False
        x = self.last_x
        y = self.last_y
        z = self.last_z

        for axis in ['x', 'y', 'z', 'e']:
            if axis in coords_dict:
                val = coords_dict[axis]
                if axis == 'z':
                    val += self.z_offset
                if axis == 'e':
                    if val > 0:
                        has_extrusion = True
                        self.cumulative_e += val
                        parts.append(f"E{self.cumulative_e:.4f}")
                else:
                    parts.append(f"{axis.upper()}{val:.2f}")
                    if axis == 'x':
                        x = val
                    elif axis == 'y':
                        y = val
                    elif axis == 'z':
                        z = val

        cmd = "G1" if has_extrusion else "G0"
        self.gcode.append(f"{cmd} {' '.join(parts)} {self.feed_rate}")
        self.last_x = x
        self.last_y = y
        self.last_z = z

    def run_test(self, lines):
        expected = {}
        idx = 0
        while idx < len(lines):
            line = self.strip_comments(lines[idx])
            if not line or line == 'end>':
                idx += 1
                continue

            if line.startswith('<expect'):
                if 'pos' in line:
                    coords = re.findall(r'([xyz])\s*[:=]\s*(-?[\w.]+)', line)
                    pos_dict = {}
                    for a, v in coords:
                        pos_dict[a] = self.resolve_val(v)
                    expected['pos'] = pos_dict
                idx += 1
                continue

            if line.startswith('<if'):
                if 'pos' in line and '@expected' in line and '!=' in line:
                    throw_match = re.search(r'throw\s*[:=]\s*"([^"]*)"', line)
                    error_msg = throw_match.group(1) if throw_match else "Test assertion failed"
                    if 'pos' in expected:
                        exp = expected['pos']
                        if 'x' in exp and abs(exp['x'] - self.last_x) > 0.001:
                            raise RuntimeError(f"{error_msg}: expected x={exp['x']}, got x={self.last_x}")
                        if 'y' in exp and abs(exp['y'] - self.last_y) > 0.001:
                            raise RuntimeError(f"{error_msg}: expected y={exp['y']}, got y={self.last_y}")
                        if 'z' in exp and abs(exp['z'] - self.last_z) > 0.001:
                            raise RuntimeError(f"{error_msg}: expected z={exp['z']}, got z={self.last_z}")
                idx += 1
                continue

            idx += 1

    def process_testmodule(self, lines):
        idx = 0
        while idx < len(lines):
            line = self.strip_comments(lines[idx])
            if not line or line == 'end>':
                idx += 1
                continue

            if line.startswith('<test'):
                test_lines = []
                idx += 1
                depth = 1
                while idx < len(lines):
                    sub_line = self.strip_comments(lines[idx])
                    if sub_line.startswith('<test'):
                        depth += 1
                    elif sub_line == 'end>':
                        depth -= 1
                        if depth == 0:
                            break
                    test_lines.append(lines[idx])
                    idx += 1
                if depth != 0:
                    raise SyntaxError("Unclosed <test> block: missing end>")
                self.run_test(test_lines)
                idx += 1
                continue

            idx += 1

    def process_block(self, lines, z_offset=None):
        old_z = self.z_offset
        if z_offset is not None:
            self.z_offset = z_offset

        idx = 0
        while idx < len(lines):
            raw_line = lines[idx]
            line = self.strip_comments(raw_line)

            if not line:
                idx += 1
                continue

            if line.startswith('<module') or line == 'end>':
                idx += 1
                continue

            if line.startswith('<testmodule'):
                test_lines = []
                idx += 1
                depth = 1
                while idx < len(lines):
                    sub_line = self.strip_comments(lines[idx])
                    if sub_line.startswith('<testmodule'):
                        depth += 1
                    elif sub_line == 'end>':
                        depth -= 1
                        if depth == 0:
                            break
                    test_lines.append(lines[idx])
                    idx += 1
                if depth != 0:
                    raise SyntaxError("Unclosed <testmodule> block: missing end>")
                self.process_testmodule(test_lines)
                idx += 1
                continue

            if line.startswith('<var'):
                match = re.search(r'(\w+)\s*[:=]\s*(-?[\w.]+)', line)
                if match:
                    self.variables[match.group(1)] = match.group(2)
                idx += 1
                continue

            if line.startswith('<temperature'):
                nozzle_match = re.search(r'nozzle\s*[:=]\s*(-?[\w.]+)', line)
                bed_match = re.search(r'bed\s*[:=]\s*(-?[\w.]+)', line)
                if nozzle_match:
                    noz_val = self.resolve_val(nozzle_match.group(1))
                    self.gcode.append(f"M109 S{noz_val:.0f}")
                if bed_match:
                    bed_val = self.resolve_val(bed_match.group(1))
                    self.gcode.append(f"M190 S{bed_val:.0f}")
                idx += 1
                continue

            if line.startswith('<fan'):
                speed_match = re.search(r'speed\s*[:=]\s*(-?[\w.]+)', line)
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
                for_match = re.search(r'@for\s+(-?[\w.]+)', line)
                zstep_match = re.search(r'@zstep\s+(-?[\w.]+)', line)
                iterations = int(self.resolve_val(for_match.group(1))) if for_match else 1
                z_step_val = self.resolve_val(zstep_match.group(1)) if zstep_match else 0.0

                loop_lines = []
                idx += 1
                depth = 1
                while idx < len(lines):
                    sub_line = self.strip_comments(lines[idx])
                    if sub_line.startswith('<loop'):
                        depth += 1
                    elif sub_line == 'end>':
                        depth -= 1
                        if depth == 0:
                            break
                    loop_lines.append(lines[idx])
                    idx += 1

                if depth != 0:
                    raise SyntaxError("Unclosed <loop> block: missing end>")

                for i in range(iterations):
                    current_z = self.z_offset + (i * z_step_val)
                    if z_step_val > 0 and current_z > self.last_z + 0.001:
                        self.gcode.append(f"G1 Z{current_z:.2f} {self.feed_rate}")
                        self.last_z = current_z
                    self.process_block(loop_lines, current_z)

                idx += 1
                continue

            if '@PREDEF CIRCLE' in line:
                match = re.search(r'r\s*[:=]\s*(-?[\w.]+)', line)
                if match:
                    r = self.resolve_val(match.group(1))
                    self.add_circle(r)
                idx += 1
                continue

            if '@PREDEF SQUARE' in line:
                match = re.search(r'size\s*[:=]\s*(-?[\w.]+)', line)
                if match:
                    s = self.resolve_val(match.group(1))
                    self.add_square(s)
                idx += 1
                continue

            if '<path' in line or '<polygon' in line:
                coords = re.findall(r'([xyze])\s*[:=]\s*(-?[\w.]+)', line)
                if coords:
                    coords_dict = {axis: self.resolve_val(val) for axis, val in coords}
                    self.emit_move(coords_dict)

            idx += 1

        self.z_offset = old_z

    def transpile(self, input_file):
        if not (input_file.endswith('.xgml') or input_file.endswith('.xgm')):
            print("ERR: File must have .xgml or .xgm extension")
            return

        if input_file.endswith('.xgml'):
            output_file = input_file.rsplit('.xgml', 1)[0] + '.gcode'
        else:
            output_file = input_file.rsplit('.xgm', 1)[0] + '.gcode'

        try:
            with open(input_file, 'r') as f:
                lines = f.readlines()
        except FileNotFoundError:
            print(f"ERR: File {input_file} not found.")
            return

        self.gcode = ["G28", "G90", "M82", "G92 E0"]
        self.feed_rate = "F3000"
        self.z_offset = 0.0
        self.cumulative_e = 0.0
        self.last_x = 0.0
        self.last_y = 0.0
        self.last_z = 0.0

        self.process_block(lines)

        with open(output_file, 'w') as f:
            f.write("\\n".join(self.gcode) + "\\n")
        print(f"Success: {output_file} generated.")


def main():
    if len(sys.argv) > 1:
        transpiler = XGMLTranspiler()
        transpiler.transpile(sys.argv[1])
    else:
        print("Usage: xgml <filename.xgml>")


if __name__ == "__main__":
    main()