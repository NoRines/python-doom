import pygame
from pygame import display, event, time
from pygame.constants import QUIT

def main():
    w, h = 640, 480

    pygame.init()

    screen = display.set_mode((w,h))
    clock = time.Clock()

    running = True
    while running:
        for e in event.get():
            if e.type == QUIT:
                running = False
    
        display.update()
        clock.tick(60)
        display.set_caption('doom-py %0.1f fps' % clock.get_fps())

    pygame.quit()

if __name__ == '__main__':
    main()