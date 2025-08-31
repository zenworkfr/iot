import random
import uasyncio as asyncio

from src import ws2812b
from src import LEDBlock2 as LEDBlock

COLORS_RGB = [
    (255, 0, 0), (0, 255, 0), (0, 0, 255),
    (255, 255, 255), (255, 0, 255),
    (255, 255, 0), (0, 255, 255),
] 

COLORS = [16711680, 65280, 255, 16777215, 16711935, 16776960, 65535]


class ZenOutput:
    def __init__(self, name):
        self.name = name
        #print("ZenOutput créé avec le nom :", name)
    
    #TODO Ca apelle self.pixels.
    def set_all(self, color):
        res = []
        b = self.leds.pixels
        for i in range(0,len(b)):
            a = self.rvb_to_dec(color)
            res.append(a)
        return res
        
    def rvb_to_dec(self, color):
        return (color[0] << 16) + (color[1] << 8) + color[2]

    def mixscenecoef(self, res_initial, res_final,t):
        res = []
        if t == 0 :
            res = res_final
        elif t == 1:
            res = res_initial
        else:   
            for color_a, color_b in zip(res_initial, res_final):
                res_calcul = self.mixpixcoef(color_a, color_b,t)
                res.append(res_calcul)
        return res
        
    
    def mixpixcoef(self, color_a, color_b, coef):
        # Extraire RGB de color_a
        a_r = (color_a >> 16) & 0xFF
        a_g = (color_a >> 8) & 0xFF
        a_b = color_a & 0xFF

        # Extraire RGB de color_b
        b_r = (color_b >> 16) & 0xFF
        b_g = (color_b >> 8) & 0xFF
        b_b = color_b & 0xFF

        # Mélange linéaire des composantes (interpolation)
        res_r = int(max(a_r * coef , b_r * (1 - coef)))
        res_g = int(max(a_g * coef , b_g * (1 - coef)))
        res_b = int(max(a_b * coef , b_b * (1 - coef)))

        # Recomposer en couleur 24 bits
        mixed_color = (res_r << 16) + (res_g << 8) + res_b
        return mixed_color

    async def fade(self, res_final, steps, duration, buffer_scenes, on):
        print("debut_fade")
        if steps==0:
            steps = 1
        mytime = duration / steps
        #coef = 0
        t = 1 / (steps+1) 
        for step in range(steps+1):
            coef = step / (steps+1) 
            res = []
            res_initial = list(self.leds.pixels)
            
            res = self.mixscenecoef(res_final, res_initial ,coef)
            #print("coef : " + str(coef) + " " + str(res))
            buffer_scenes[:] = res
            await asyncio.sleep(mytime)
        res = self.mixscenecoef(res_final, res_initial ,1)
        #print("coef : " + str(1) + " " + str(res))
        await asyncio.sleep(mytime)
        await asyncio.sleep(on)

class ZenOutput4x4(ZenOutput):
    
    PATERNS = {    "black": "XXXXXXXXXXXXXXXX",
                    "centre": "BBBBBAABBAABBBBB",
                    "cotes": "ABBABBBBBBBBABBA",
                    "grandX": "ABBABAABBAABABBA",
                    "rond": "BAABABBAABBABAAB",
                    "jesus1": "BBABAAABBBABBABB",
                    "jesus2": "BABBBAAABABBBBAB",
                    "hauteur1": "ABBBBBBAABBBBBBA",
                    "hauteur2": "BABBBBABBABBBBAB",
                    "hauteur3": "BBABBABBBBABBABB",
                    "hauteur4": "BBBAABBBBBBAABBB",
                    "vertical1": "AAAABBBBBBBBBBBB",
                    "vertical2": "BBBBAAAABBBBBBBB",
                    "vertical3": "BBBBBBBBAAAABBBB",
                    "vertical4": "BBBBBBBBBBBBAAAA",
                    "full": "AAAAAAAAAAAAAAAA",
                    "hauteur12_34": "AABBBBAAAABBBBAA",
                    "hauteur13_24": "ABABBABAABABBABA",
                    "vertical12_34": "AAAAAAAABBBBBBBB",
                    "vertical13_24": "AAAABBBBAAAABBBB"
                }

    
    def __init__(self, LED_PIN = 28):
        self.blocks = []
        current_index = 0
        self.LED_PIN = LED_PIN
        self.name = "4x4"
        self.composition = [LEDBlock.Block8LED, LEDBlock.Block8LED, LEDBlock.Block8LED, LEDBlock.Block8LED,
                        LEDBlock.Block8LED, LEDBlock.BlockMiroirInfini, LEDBlock.Block8LED, LEDBlock.Block8LED,
                        LEDBlock.Block8LED, LEDBlock.Block8LED, LEDBlock.Block8LED, LEDBlock.Block8LED,
                        LEDBlock.Block8LED, LEDBlock.Block8LED, LEDBlock.Block8LED, LEDBlock.Block8LED,]
        
        #self.composition = [LEDBlock.Block8LED, LEDBlock.Block8LED]
        for cls in self.composition:
            block = cls(current_index)
            self.blocks.append(block)
            current_index += block.size
            if isinstance(block, LEDBlock.BlockMiroirInfini):
                miroir = block
        # initialisation du buffer & LEDs
        self.NB_LEDS = sum(b.size for b in self.blocks)
        #print(self.NB_LEDS)
        buffer = [(0,0,0)] * self.NB_LEDS
        self.leds = ws2812b.ws2812b(self.NB_LEDS, 0, LED_PIN)
        self.leds.fill(0,0,0)
        self.show()
 
    def full(self, patern, color1, color2):
        #patern = "XXAXAAAXXXAXXAXX"
        #print("full patern " + patern + str(color1) + str(color2))
        res = []
        block = 0
        if color1=="RAND":
            color1 = random.choice(COLORS_RGB)
        if color2:
            if color2 == "RAND":
                color2 = random.choice(COLORS_RGB)
                print("color2")
                for car in patern:
                    if car == "A":
                        a = [self.rvb_to_dec(color1)] * self.blocks[block].size
                    elif car == "B":
                        a = [self.rvb_to_dec(color2)] * self.blocks[block].size
                    elif car == "X":
                        a = [0] * self.blocks[block].size
                    res = res + a  
                    block += 1
            else:
                for car in patern:
                    if car == "A":
                        a = [self.rvb_to_dec(color1)] * self.blocks[block].size
                    elif car == "B":
                        a = [self.rvb_to_dec(color2)] * self.blocks[block].size
                    elif car == "X":
                        a = [0] * self.blocks[block].size
                    res = res + a  
                    block += 1
            #print(res)
            
        return res;
    
    async def prg_4x4_sympa(self, color1, color2, step_on, duration_on, buffer_scenes, delay):
        await self.fade(self.full(self.PATERNS["centre"], color1, color2), step_on, duration_on, buffer_scenes, delay)
        await self.fade(self.full(self.PATERNS["cotes"], color1, color2), step_on, duration_on, buffer_scenes, delay)
        await self.fade(self.full(self.PATERNS["grandX"], color1, color2), step_on, duration_on, buffer_scenes, delay)
        await self.fade(self.full(self.PATERNS["rond"], color1, color2), step_on, duration_on, buffer_scenes, delay)
        await self.fade(self.full(self.PATERNS["jesus1"], color1, color2), step_on, duration_on, buffer_scenes, delay)
        await self.fade(self.full(self.PATERNS["jesus2"], color1, color2), step_on, duration_on, buffer_scenes, delay)
        await self.fade(self.full(self.PATERNS["vertical1"], color1, color2), int(step_on/4), int(duration_on/4), buffer_scenes, int(delay/4))
        await self.fade(self.full(self.PATERNS["vertical2"], color1, color2), int(step_on/4), int(duration_on/4), buffer_scenes, int(delay/4))
        await self.fade(self.full(self.PATERNS["vertical3"], color1, color2), int(step_on/4), int(duration_on/4), buffer_scenes, int(delay/4))
        await self.fade(self.full(self.PATERNS["vertical4"], color1, color2), int(step_on/4), int(duration_on/4), buffer_scenes, int(delay/4))
        await self.fade(self.full(self.PATERNS["vertical3"], color1, color2), int(step_on/4), int(duration_on/4), buffer_scenes, int(delay/4))
        await self.fade(self.full(self.PATERNS["vertical2"], color1, color2), int(step_on/4), int(duration_on/4), buffer_scenes, int(delay/4))
        await self.fade(self.full(self.PATERNS["vertical1"], color1, color2), int(step_on/4), int(duration_on/4), buffer_scenes, int(delay/4))
        await self.fade(self.full(self.PATERNS["grandX"], color1, color2), step_on, duration_on, buffer_scenes, delay)
        await self.fade(self.full(self.PATERNS["hauteur1"], color1, color2), int(step_on/4), int(duration_on/4), buffer_scenes, int(delay/4))
        await self.fade(self.full(self.PATERNS["hauteur2"], color1, color2), int(step_on/4), int(duration_on/4), buffer_scenes, int(delay/4))
        await self.fade(self.full(self.PATERNS["hauteur3"], color1, color2), int(step_on/4), int(duration_on/4), buffer_scenes, int(delay/4))
        await self.fade(self.full(self.PATERNS["hauteur4"], color1, color2), int(step_on/4), int(duration_on/4), buffer_scenes, int(delay/4))
        await self.fade(self.full(self.PATERNS["hauteur3"], color1, color2), int(step_on/4), int(duration_on/4), buffer_scenes, int(delay/4))
        await self.fade(self.full(self.PATERNS["hauteur2"], color1, color2), int(step_on/4), int(duration_on/4), buffer_scenes, int(delay/4))
        await self.fade(self.full(self.PATERNS["hauteur1"], color1, color2), int(step_on/4), int(duration_on/4), buffer_scenes, int(delay/4))
        await self.fade(self.full(self.PATERNS["grandX"], color1, color2), step_on, duration_on, buffer_scenes, delay)
        
        await self.fade(self.full(self.PATERNS["hauteur12_34"], color1, color2), step_on, duration_on, buffer_scenes, delay)
        await self.fade(self.full(self.PATERNS["hauteur12_34"], color2, color1), step_on, duration_on, buffer_scenes, delay)
        await self.fade(self.full(self.PATERNS["hauteur12_34"], color1, color2), step_on, duration_on, buffer_scenes, delay)
        await self.fade(self.full(self.PATERNS["hauteur12_34"], color2, color1), step_on, duration_on, buffer_scenes, delay)
        
        await self.fade(self.full(self.PATERNS["hauteur13_24"], color1, color2), step_on, duration_on, buffer_scenes, delay)
        await self.fade(self.full(self.PATERNS["hauteur13_24"], color2, color1), step_on, duration_on, buffer_scenes, delay)
        await self.fade(self.full(self.PATERNS["hauteur13_24"], color1, color2), step_on, duration_on, buffer_scenes, delay)
        await self.fade(self.full(self.PATERNS["hauteur13_24"], color2, color1), step_on, duration_on, buffer_scenes, delay)
        
        await self.fade(self.full(self.PATERNS["vertical12_34"], color1, color2), step_on, duration_on, buffer_scenes, delay)
        await self.fade(self.full(self.PATERNS["vertical12_34"], color2, color1), step_on, duration_on, buffer_scenes, delay)
        await self.fade(self.full(self.PATERNS["vertical12_34"], color1, color2), step_on, duration_on, buffer_scenes, delay)
        await self.fade(self.full(self.PATERNS["vertical12_34"], color2, color1), step_on, duration_on, buffer_scenes, delay)
        
        await self.fade(self.full(self.PATERNS["vertical13_24"], color1, color2), step_on, duration_on, buffer_scenes, delay)
        await self.fade(self.full(self.PATERNS["vertical13_24"], color2, color1), step_on, duration_on, buffer_scenes, delay)
        await self.fade(self.full(self.PATERNS["vertical13_24"], color1, color2), step_on, duration_on, buffer_scenes, delay)
        await self.fade(self.full(self.PATERNS["vertical13_24"], color2, color1), step_on, duration_on, buffer_scenes, delay)
       
        await self.fade(self.full(self.PATERNS["full"], color1, color2), int(step_on/4), int(duration_on/4), buffer_scenes, delay*2)
        await self.fade(self.full(self.PATERNS["black"], color1, color2), int(step_on/4), int(duration_on/4), buffer_scenes, delay)

    def show(self):
        self.leds.show()