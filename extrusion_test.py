import math
from PIL import Image, ImageDraw, ImageFont

class SimpleGCodeWriter:
    def __init__(self, file_name: str, is_volumetric: bool = False, nozzle_size: float = 0.4, layer_height = 0.25):
        self.current_x = 0
        self.current_y = 0
        self.current_extrusion_length = 0

        # TODO user input
        self.nozzle_size = nozzle_size
        self.layer_height = layer_height
        self.filament_diameter = 2.85

        self.is_volumetric = is_volumetric
        self.file_name = file_name
        self.file = None
    
    def __enter__(self):
        self.file = open(self.file_name, "w")
        return self

    def __exit__(self, type, value, traceback):
        self.file.close()

    def move(self, x: float = None, y: float = None, z: float = None, feedrate: float = None):
        params = {}

        if x is not None:
            self.current_x = x
            params["X"] = x

        if y is not None:
            self.current_y = y
            params["Y"] = y

        if z is not None:
            params["Z"] = z
        
        if feedrate is not None:
            params["F"] = feedrate

        self.write_code("G0", params)

    def extrude(self, x: float, y: float):
        path_length = ((x - self.current_x) ** 2 + (y - self.current_y) ** 2) ** (1 / 2)
        volume = self.nozzle_size * self.layer_height * path_length # roughly a rectangular prism

        self.current_x = x
        self.current_y = y

        if self.is_volumetric:
            self.current_extrusion_length += volume
        else:
            filament_area = (filament_diameter / 2) ** 2 * math.pi
            extrusion_length = volume / filament_area
            self.current_extrusion_length += extrusion_length

        self.write_code("G1", { "X": self.current_x, "Y": self.current_y, "E": self.current_extrusion_length })
    
    def set_fan_speed(self, speed: int):
        self.write_code("M106", { "S": speed })

    def write_code(self, code: str, params: dict):
        self.write_line(code + " " + " ".join(key + str(value) for (key, value) in params.items()))
    
    def write_comment(self, comment: str):
        self.write_line("; " + comment)
    
    def write_line(self, line: str):
        self.file.write(line + "\n")

filament_diameter = 2.85
layer_height = 0.25
nozzle_size = 0.4
radius = 30
layer = 1

resolution = int(10 / layer_height)

with SimpleGCodeWriter("D:\\patate.gcode", is_volumetric=True, nozzle_size=nozzle_size, layer_height=layer_height) as w:
    w.write_line(";FLAVOR:UltiGCode\n;TIME:0\n;MATERIAL:1\n;MATERIAL2:0\n;NOZZLE_DIAMETER:{}\n".format(nozzle_size))
    w.move(111.5 + 30, 111.5)

    for i in range(7, 11):
        w.write_line("M106 S255") # fan speed

        feedrate = i / (layer_height * nozzle_size) * 60

        w.write_comment("{} mm^3/s".format(i))
        w.move(feedrate=feedrate)

        font = ImageFont.truetype("C:\Windows\Fonts\consola.ttf", size=int(resolution * 0.8))
        size = font.getsize(str(i) + " mm³/s")
        img = Image.new('RGB', (size[0], resolution), color = (0, 0, 0))
        d = ImageDraw.Draw(img)
        d.text((0, (resolution - size[1]) / 2), str(i) + " mm³/s", fill=(255, 255, 255), font=font)
            
        for j in range(math.ceil(10 / layer_height)):
            w.write_comment("LAYER " + str(layer))
            w.move(z=layer_height * layer)
            circumference = 2 * radius * math.pi
            current_pos = 0
            min_pos = circumference * 0.75 - layer_height * img.width / 2
            max_pos = circumference * 0.75 + layer_height * img.width / 2
            prev_dist = 0
            last_point = 0

            while (current_pos < circumference):
                dist = radius
                next_dist = radius

                if current_pos >= min_pos and current_pos < max_pos:
                    x = int((current_pos - min_pos) / layer_height)
                    value = img.getpixel((x, img.height - j - 1))[0]
                    dist = radius - value / 255 * nozzle_size * 2

                    if x < img.width - 1:
                        next_dist = radius - img.getpixel((x + 1, img.height - j - 1))[0] / 255 * nozzle_size * 2
                
                current_pos += layer_height

                if dist != prev_dist or current_pos - last_point > 2 or current_pos >= circumference or next_dist != dist:
                    angle = (min(current_pos / circumference, 1) * 2 * math.pi)

                    x = math.cos(angle) * dist + 111.5
                    y = math.sin(angle) * dist + 111.5
                    w.extrude(x, y)

                    last_point = current_pos

                prev_dist = dist
            
            layer += 1
        
        w.move(z=layer_height * layer)

        for k in range(101):
            x = math.cos(math.pi * 2 / 100 * k) * (radius - nozzle_size / 2) + 111.5
            y = math.sin(math.pi * 2 / 100 * k) * (radius - nozzle_size / 2) + 111.5
            w.extrude(x, y)
        
        layer += 1