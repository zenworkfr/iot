import uasyncio as asyncio


# === Classe de base LEDBlock ===
class LEDBlock:
    def set_layer(self, name, color_list):
        # ajoute ou met à jour une couche (fade, flash, spin...)
        self.active_layers[name] = color_list

    def clear_layer(self, name):
        if name in self.active_layers:
            del self.active_layers[name]
    
    def __init__(self, indices):
        self.indices = indices
        self.size = len(indices)
        self.active_layers = {}  # couche_name -> list[(r,g,b)]
        self.active_scene = False

    async def fade(self, color, fade_in=True, steps=30, delay=0.05):
        for step in range(steps + 1):
            t = step / steps if fade_in else (1 - step / steps)
            rgb = (int(color[0]*t), int(color[1]*t), int(color[2]*t))
            self.set_layer('fade', [rgb]*self.size)
            await asyncio.sleep(delay)
        if not fade_in:
            self.clear_layer('fade')

# === Sous-classes de blocs ===
class Block8LED(LEDBlock):
    def __init__(self, start_index):
        super().__init__([start_index + i for i in range(8)])

class Block6LED(LEDBlock):
    def __init__(self, start_index):
        super().__init__([start_index + i for i in range(6)])
        
class BlockMiroirInfini(LEDBlock):
    def __init__(self, start_index):
        super().__init__([start_index + i for i in range(36)])
        
    async def spinning_effect(self, color=(0,0,255), delay=1):
        while True:
            for i in range(self.size/4):
                frame = [(0,0,0)]*self.size
                frame[i] = color
                frame[18-i-1] = color
                frame[18+i] = color
                frame[36-i-1] = color
                
                self.set_layer('spin', frame)
                await asyncio.sleep(delay)






                        