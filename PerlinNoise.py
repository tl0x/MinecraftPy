import matplotlib.pyplot as plt
from perlin_noise import PerlinNoise

def GenerateHeightMap(seed,size):
    noise1 = PerlinNoise(octaves=8,seed=seed)
    noise2 = PerlinNoise(octaves=8,seed=seed)
    noise3 = PerlinNoise(octaves=6,seed=seed)
    Heights = []
    WaterLevel = -32

    for x in range(size):
        row = []
        for z in range(size):
            heightResult = 0
            heightLow = (noise1([x * 1.3, z * 1 / 3])*3) - 4
            heightHigh = (noise2([x * 1.3, z * 1 / 3])*12) + 6
            if noise3([x, z]) / 8 > 0:
                heightResult = heightLow
            else:
                heightResult = heightHigh
            heightResult /= 2
            if heightResult < 0:
                heightResult *= 0.8
            row.append(round(heightResult))
        Heights.append(row)
    return Heights