# Подключаем библиотеки:
import time
import krpc
import numpy as np
import matplotlib.pyplot as plt
import math

# Объявляем необходимые переменные:
g0 = 9.81
m_topliva = 72200
m_rakety = 68020
r0 = 1.2255
M = 0.02898
R = 8.314
T = 287
earth_mass = 5.292e22
earth_rad = 600000
moon_mass = 9.76e20
moon_rad = 200000
moon_to_earth = 11400000
g_bol = 6.67e-11

# Создаём подключение к серверу:
conn = krpc.connect(name='Lunohod')
vessel = conn.space_center.active_vessel
srf_frame = vessel.orbit.body.reference_frame

# Открываем потоки для считывания данных:
ut = conn.add_stream(getattr, conn.space_center, 'ut')
altitude = conn.add_stream(getattr, vessel.flight(), 'mean_altitude')
srf_speed = conn.add_stream(getattr, vessel.flight(srf_frame), 'speed')
impulse = conn.add_stream(getattr, vessel, "specific_impulse")
thrust = conn.add_stream(getattr, vessel, "thrust")
ksp_mass = conn.add_stream(getattr, vessel, "mass")
stage_3_resources = vessel.resources_in_decouple_stage(stage=3, cumulative=False)
srb_fuel_stage3 = conn.add_stream(stage_3_resources.amount, 'LiquidFuel')


# Задаём функцию, рассчитывающую массу и ускорение по формулам математической и физической модели:
def f(alt):
    if srb_fuel_stage3() > 0:
        m_top_cur = 54000
        m_rak_cur = 68020
    else:
        m_rak_cur = 15320
        m_top_cur = 9000
    global impulse, g0, m_topliva, m_rakety, thrust, g_bol, earth_mass, earth_rad, moon_mass, moon_rad, moon_to_earth
    m = m_top_cur + m_rak_cur - impulse() * g0 * math.log(1 + (m_top_cur / m_rak_cur))
    if alt != 0:
        a = thrust() / m - (g_bol * earth_mass) / (earth_rad + alt) ** 2
        return a
    else:
        return 0


# Задаём функцию, рассчитывающую скорость по математической и физической модели:
def speed_mm(a, v0):
    v = v0 + a * 0.5
    return v


# Задаём функцию, рассчитывающую ускорение по данным из KSP:
def acceleration(v, v0):
    result = (v - v0) / 2
    return result


# Задаём переменые, необходимые для хранения данных:
h = np.linspace(0, 60000, num=280)
a_array = []
altitude_array = []
speed_array = []
i = 0
k = 0
minus = ut()
speed_mm_array = [0]

# Задаём цикл по времени полёта (в нашем случае экспериментально подобрано время, необходимое для выхода ракеты на
# орбину Кербина):

while i < 140:
    mass = m_topliva + m_rakety - impulse() * g0 * math.log(1 + (m_topliva / m_rakety))
    print(thrust(), (g_bol * earth_mass) / ((earth_rad + altitude()) ** 2),
          thrust() / mass - (g_bol * earth_mass) / (earth_rad + altitude()) ** 2)
    # print(mass)
    # print(ksp_mass())
    altitude_array.append(altitude())
    a_array.append(f(h[k]))
    speed_mm_array.append(speed_mm(a_array[-1], speed_mm_array[-1]))
    speed_array.append(srf_speed())
    time.sleep(0.5)
    i += 0.5
    k += 1


# Удалим первый элемент массива скорости, добавленый изначально для рассчёта:

del speed_mm_array[0]

# Просчитаем ускорение по данным из KSP:
ac_array = [speed_array[0] / 2]
for j in range(1, len(speed_array)):
    ac_array.append(acceleration(speed_array[j], speed_array[j - 1]))

# Построим график зависимости ускорения от высоты по данным из KSP:
plt.plot(altitude_array, ac_array, color="purple")
plt.plot(h, a_array, color="red")
plt.xlabel('altitude, м')
plt.ylabel('a, m/s^2')
plt.grid(color='black')
plt.show()

# Построим график зависимости скорости от высоты по данным из KSP:
plt.plot(altitude_array, speed_array, color="purple")
plt.plot(h, speed_mm_array, color="red")
plt.xlabel('altitude, м')
plt.ylabel('v, m/s')
plt.grid(color='black')
plt.show()

