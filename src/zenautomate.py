from machine import Pin
import array
import random
import uasyncio as asyncio
COLORS_RGB = [
    (255, 0, 0), (0, 255, 0), (0, 0, 255),
    (255, 255, 255), (255, 0, 255),
    (255, 255, 0), (0, 255, 255),
] 

COLORS = [16711680, 65280, 255, 16777215, 16711935, 16776960, 65535]

class ZenAutomate:
    def __init__(self, input_obj, time_step=1):
        self.input_obj = input_obj
        self.time_step = time_step
        black = [0] * self.input_obj.NB_LEDS
        self.buffer_scenes = black[:]
        self.buffer_scintillement = black[:]
        self.buffer_mirroirRun = black[:]
        self.buffer = black[:]
        self.buffer_start_scenes = black[:]
        self.pin_running_alone = Pin(13, Pin.IN, Pin.PULL_UP)
        self.pin_starting = Pin(12, Pin.IN, Pin.PULL_UP)
        self.pin_mirroir = Pin(11, Pin.IN, Pin.PULL_UP)
        
    async def scene_controller(self):
        """
        Gère les scènes dynamiquement selon les états GPIO
        """
        active_tasks = {}
        MAX_ACTIVE = 6
        while True:
            # Nettoyage des tâches terminées (au cas où)
            to_remove = [key for key, task in active_tasks.items() if task.done()]
            for key in to_remove:
                del active_tasks[key]

            # running_alone
            if self.running_alone and not any(f"random_scint{x}" in active_tasks for x in range(MAX_ACTIVE)):
                print("Démarrage random_scint")
                tasks =[]
                for i in range(MAX_ACTIVE):
                    task = asyncio.create_task(self.random_scintillement())
                    active_tasks["random_scint" + str(i)] = task
            elif not self.running_alone and any(f"random_scint{x}" in active_tasks for x in range(MAX_ACTIVE)):
                print("Arrêt random_scint")
                self.buffer_scintillement = self.input_obj.set_all((0,0,0))
                for i in range(MAX_ACTIVE):
                    active_tasks["random_scint" + str(i)].cancel()
                del active_tasks["random_scint" + str(i)]

            # starting
            if self.starting_state == 0:
                self.buffer_scenes = self.input_obj.set_all((0,0,0))
                
            if self.starting_state == 1:
                if "prg1" not in active_tasks:
                    print("Démarrage prg1")
                    self.buffer_scenes = self.input_obj.set_all((0,0,0))
                    self.buffer_scenes = self.input_obj.set_all((0,0,0))
                    task = asyncio.create_task(self.demo(color1 = "RAND", color2=(0,0,0),
                                                         step_on=100, duration_on = 3, buffer_scenes=self.buffer_scenes, delay=5))
                    active_tasks["prg1"] = task
            else:
                if "prg1" in active_tasks:
                    print("Arrêt prg1")
                    self.buffer_scenes = self.input_obj.set_all((0,0,0))
                    active_tasks["prg1"].cancel()
                    del active_tasks["prg1"]

            if self.starting_state == 2:
                if "prg2" not in active_tasks:
                    print("Démarrage prg2")
                    self.buffer_scenes = self.input_obj.set_all((0,0,0))
                    task = asyncio.create_task(self.demo(color1 = "RAND", color2=(0,0,0),
                                                         step_on=1, duration_on = 0.2, buffer_scenes=self.buffer_scenes, delay=0.5))
                    active_tasks["prg2"] = task
            else:
                if "prg2" in active_tasks:
                    print("Arrêt prg2")
                    self.buffer_scenes = self.input_obj.set_all((0,0,0))
                    active_tasks["prg2"].cancel()
                    del active_tasks["prg2"]

            if self.starting_state == 3:
                if "prg3" not in active_tasks:
                    print("Démarrage prg3")
                    self.buffer_scenes = self.input_obj.set_all((0,0,0))
                    task = asyncio.create_task(self.demo(color1 = "RAND", color2=(0,0,0),
                                                         step_on=100, duration_on = 200, buffer_scenes=self.buffer_scenes, delay=500))
                    active_tasks["prg3"] = task
            else:
                if "prg3" in active_tasks:
                    print("Arrêt prg3")
                    self.buffer_scenes = self.input_obj.set_all((0,0,0))
                    active_tasks["prg3"].cancel()
                    del active_tasks["prg3"]
            # mirroir
            if self.mirroir and "mirroir" not in active_tasks:
                print("Démarrage mirroir")
                task = asyncio.create_task(self.mirroirRun(1))
                active_tasks["mirroir"] = task
            elif not self.mirroir and "mirroir" in active_tasks:
                print("Arrêt mirroir")
                self.buffer_mirroirRun = self.input_obj.set_all((0,0,0))
                active_tasks["mirroir"].cancel()
                del active_tasks["mirroir"]

            await asyncio.sleep(0.2)


    async def monitor_switches(self, delay_ms=100):
        """
        Surveille les GPIO et inverse l'état au clic (toggle)
        """
        prev_running_alone = 1
        prev_starting = 1
        self.starting_state = 0   # 0=stop, 1=prg1, 2=prg2, ...
        prev_mirroir = 1

        # États initiaux
        self.running_alone = False
        self.starting = False
        self.mirroir = False

        while True:
            cur_running_alone = self.pin_running_alone.value()
            cur_starting = self.pin_starting.value()
            cur_mirroir = self.pin_mirroir.value()
            

            # running_alone toggle
            if prev_running_alone == 1 and cur_running_alone == 0:
                self.running_alone = not self.running_alone
                print("running_alone =", self.running_alone)

            # starting toggle
            if prev_starting == 1 and cur_starting == 0:
                self.starting_state = (self.starting_state + 1) % 4 
                #self.starting = not self.starting
                print("starting =", self.starting_state)

            # mirroir toggle
            if prev_mirroir == 1 and cur_mirroir == 0:
                self.mirroir = not self.mirroir
                print("mirroir =", self.mirroir)

            prev_running_alone = cur_running_alone
            prev_starting = cur_starting
            prev_mirroir = cur_mirroir

            await asyncio.sleep_ms(delay_ms)



    async def run(self):
        print("ZenAutomate lancé")
        print(f"[{self.input_obj.name}] cycle...prg run()")
        # Lancer la surveillance des GPIO
        asyncio.create_task(self.monitor_switches())
        tasks = []
        # Tâches dynamiques réactives
        tasks.append(asyncio.create_task(self.scene_controller()))
        tasks.append(asyncio.create_task(self.show(0.05)))
        await asyncio.gather(*tasks)
      
      
    #**********************************************************************************
    def rvb_to_dec(color):
        return (color[0] << 16) + (color[1] << 8) + color[2]
        
    def force(self, a,b):
        return a if any(c != 0 for c in a) else b

    def mix(self, a, b):
        # Vérifie que les deux buffers ont la bonne taille
        size = self.input_obj.NB_LEDS
        if len(a) != size:
            a = [0] * size
        if len(b) != size:
            b = [0] * size

        res = []
        for color_a, color_b in zip(a, b):
            # Extraire les composantes RGB
            a_r = (color_a >> 16) & 0xFF
            a_g = (color_a >> 8) & 0xFF
            a_b = color_a & 0xFF

            b_r = (color_b >> 16) & 0xFF
            b_g = (color_b >> 8) & 0xFF
            b_b = color_b & 0xFF

            # Mélange RGB (valeurs max)
            res_r = max(a_r, b_r)
            res_g = max(a_g, b_g)
            res_b = max(a_b, b_b)

            # Recompose en valeur décimale
            mixed_color = (res_r << 16) + (res_g << 8) + res_b
            res.append(mixed_color)
        return res


            
    async def fadeblock(self, block, color_initial, color_final,steps, duration):
        mytime = duration / steps
        for step in range(steps+1):
            t = 1 - step / steps
            color_compute = self.input_obj.mixpixcoef(color_initial, color_final,t)    
            #print(str(t) + " " + str(color_compute))    
            self.buffer_scintillement[block.indices[0]:block.indices[0] + block.size] = [color_compute]*block.size
            await asyncio.sleep(mytime)

    async def demo(self, color1, color2, step_on, duration_on, buffer_scenes, delay):
        print("prg demo ZenAutomate lancé")
        while True:
            buffer_scenes[:] = self.input_obj.set_all((0,0,0))
            if color1 == "RAND1TIME":
                color1 = random.choice(COLORS_RGB)
            #color2 = random.choice(COLORS_RGB)
            await self.input_obj.prg_4x4_sympa(color1, color2, step_on, duration_on, buffer_scenes, delay)
    
    async def scintillementBlock(self):
        while True:
            trouve = False
            while not(trouve):
                block = random.choice(self.input_obj.blocks)
                trouve = not(block.active_scene)
            block.active_scene = True
            color = random.choice(COLORS)
            step_on = 60
            step_off = 40
            duration_on = random.uniform(0, 5)
            on = random.uniform(1, 20)
            duration_off=random.uniform(1, 10)
            await self.fadeblock(block,0, color,step_on,duration_on)
            await asyncio.sleep(on)
            await self.fadeblock(block, color, 0,step_off,duration_off)
            block.active_scene = False
    
    
    
    async def random_scintillement(self):
        while True:
            color = random.choice(COLORS_RGB)
            await self.scintillementBlock()
    
    async def mirroirRun(self, time_step = 1, color = (-1,-1,-1)):
        print("prg ZenAutomate mirroirRun lancé")
        mysize = 9
        while True:
            res = []
            self.buffer_mirroirRun =  res
            color = random.choice(COLORS)
            for i in range(mysize):
                frame = [0]*mysize*4
                frame[i] = color
                frame[18-i-1] = color
                frame[18+i] = color
                frame[36-i-1] = color
                self.buffer_mirroirRun = [0] * 40 + frame + [0] * 80
                await asyncio.sleep(time_step)
            await asyncio.sleep(time_step)

    async def show(self, time_step = 1):
        while True:
            self.buffer[:] = self.mix(self.buffer_start_scenes,self.mix(self.buffer_mirroirRun ,self.force(self.buffer_scenes,self.buffer_scintillement)))
            self.input_obj.leds.pixels = array.array("I", self.buffer)
            self.input_obj.show()
            await asyncio.sleep(time_step)
            

