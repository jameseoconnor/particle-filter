from math import *
import random
import numpy as np
import matplotlib.pyplot as plt
from celluloid import Camera
from matplotlib import animation

class robot:
    def __init__(self):
        self.x = random.random() * world_size  # initialise with random
        self.y = random.random() * world_size
        self.orientation = random.random() * 2.0 * pi
        
        self.forward_noise = 0.0
        self.turn_noise    = 0.0
        self.sense_noise   = 0.0
        
        
    def set(self, new_x, new_y, new_orientation):
            if new_x < 0 or new_x >= world_size:
                raise ValueError('X coordinate out of bound')
            if new_y < 0 or new_y >= world_size:
                raise ValueError('Y coordinate out of bound')
            if new_orientation < 0 or new_orientation >= 2 * pi:
                raise ValueError('Orientation must be in [0..2pi]')
            self.x = float(new_x)
            self.y = float(new_y)
            self.orientation = float(new_orientation)

            
    def set_noise(self, new_f_noise, new_t_noise, new_s_noise):
        # makes it possible to change the noise parameters
        # this is often useful in particle filters
        self.forward_noise = float(new_f_noise);
        self.turn_noise    = float(new_t_noise);
        self.sense_noise   = float(new_s_noise);
        
        
    def sense(self):
        Z = []
        for i in range(len(landmarks)):
            dist = sqrt((self.x - landmarks[i][0]) ** 2 + (self.y - landmarks[i][1]) ** 2)
            dist += random.gauss(0.0, self.sense_noise)
            Z.append(dist)
        return Z
    
    
    def move(self, turn, forward):
        if forward < 0:
            raise ValueError('Robot cant move backwards')
        
        # turn, and add randomness to the turning command
        orientation = self.orientation + float(turn) + random.gauss(0.0, self.turn_noise)
        orientation %= 2 * pi
        
        # move, and add randomness to the motion command
        dist = float(forward) + random.gauss(0.0, self.forward_noise)
        x = self.x + (cos(orientation) * dist)
        y = self.y + (sin(orientation) * dist)
        x %= world_size    # cyclic truncate
        y %= world_size
        
        # set particle
        res = robot()
        res.set(x, y, orientation)
        res.set_noise(self.forward_noise, self.turn_noise, self.sense_noise)
        return res
    
    
    def Gaussian(self, mu, sigma, x):
        # calculates the probability of x for 1-dim Gaussian with mean mu and var. sigma
        return exp(- ((mu - x) ** 2) / (sigma ** 2) / 2.0) / sqrt(2.0 * pi * (sigma ** 2))
    
    
    def measurement_prob(self, measurement):
        # calculates how likely a measurement should be
        prob = 1.0
        for i in range(len(landmarks)):
            dist = sqrt((self.x - landmarks[i][0]) ** 2 + (self.y - landmarks[i][1]) ** 2)
            prob *= self.Gaussian(dist, self.sense_noise, measurement[i])
        return prob
    
    
    def __repr__(self):
        return '[x=%.6s y=%.6s orient=%.6s]' % (str(self.x), str(self.y), str(self.orientation))


def create_target(forward_noise, turn_noise, sense_noise):
    target = robot()
    target.set_noise(forward_noise, turn_noise, sense_noise)
    target.set(30., 50., pi/2)
    return target


def create_particles(num_particles):
    # initialise randomly guessed particles
    particles = []
    
    for i in range(num_particles):
        x = robot()
        x.set_noise(0.05, 0.05, 5.0)
        particles.append(x)
    return particles
    
    
def run_simulation(target, particles, runs, step_size, turn_size):
    N = len(particles)

    
    for rd in range(runs):
        plot_world(target, particles, rd, True)
        target = target.move(turn_size, step_size)
        Z = target.sense()

        particles_moved = []
        for i in range(N):
            # turn 0.1 and move 5 meters
            particles_moved.append(particles[i].move(turn_size, step_size))
        particles = particles_moved

        # given the particle's location, how likely measure it as Z
        particle_prob = []

        for particle in particles:
            prob = particle.measurement_prob(Z)  # Z remains the same
            particle_prob.append(prob)

        #   resampling particles based on probability weights
        resampled_particles = []
        index = int(random.random()*N)
        beta = 0
        mw = max(particle_prob)

        for i in range(N):
            beta += random.random() * 2.2 * mw
            while beta > particle_prob[index]:
                beta -= particle_prob[index]
                index = (index + 1)%N
            resampled_particles.append(particles[index])

        particles = resampled_particles


def plot_world(target, particles, run_no=1, show=True):
    landmark_x = []
    landmark_y = []
    particles_x = []
    particles_y = []
    
    plot_text = f"Run  {run_no+1}"
    for i in range(len(landmarks)):
        landmark_x.append(landmarks[i][0])
        landmark_y.append(landmarks[i][1])
        
    for particle in particles:
        particles_x.append(particle.x)
        particles_y.append(particle.y)
        
    plt.scatter(landmark_x, landmark_y, color="b", marker='s')
    particles_plot = plt.gca()
    particles_plot.scatter(particles_x, particles_y, color="r")
    target_plot = plt.gca()
    
    if target:
        target_plot.scatter(target.x, target.y, color="g")
        
    plt.xlim(0, world_size)
    plt.ylim(0, world_size)
    plt.text(1, 1, plot_text, fontsize=15)
    plt.xlabel("x-direction")
    plt.ylabel("y-direction")
    plt.savefig(f'snap_{run_no}.png', bbox_inches='tight')
    camera.snap()



camera = Camera(plt.figure())

# Define environment
landmarks  = [[20.0, 20.0], [80.0, 80.0], [20.0, 80.0], [80.0, 20.0]]
world_size = 100.0

# Create target with sensor noise
forward_noise = 4.0  # The noise of the forward measuring sensor (m)
turn_noise = 0.2  # The turn noise of the sensor (radians)
sense_noise = 5.0  # The noise of the distance measuring sensor (m)
target = create_target(forward_noise, turn_noise, sense_noise) # Create a target 


# Create particles
num_particles=20 # Define the number of particles to be used
particles = create_particles(num_particles) # Create a list of particles 

# Set simulation parameters and simulate 
runs = 10
step_size = 1
turn_size = 0.4
run_simulation(target, particles, runs, step_size, turn_size)

# Create GIF
anim = camera.animate(blit=False)
writergif = animation.PillowWriter(fps=2) 
anim.save('scatter_3.gif', writer=writergif)


particle_single = []
x = robot()
x.set_noise(0.05, 0.05, 5.0)
particle_single.append(x)
plot_world(target, particle_single, 0)


target_measurement = [28.954898, 55.8679245,  53.9708025, 29.2746963]# 
mu = 12.445
x = 28.9548
sigma = 5
result = exp(- ((mu - x) ** 2) / (sigma ** 2) / 2.0) / sqrt(2.0 * pi * (sigma ** 2))
print(result)