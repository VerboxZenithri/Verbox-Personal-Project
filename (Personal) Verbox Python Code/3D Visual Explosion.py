import time
import sys
import winsound

def nuke(n):  #Nah Ini Bomb Nya
    a=[]
    for i in range(255):
        if n>1:
            a.append(nuke(n-1))
        else:
            a.append(i)
    return a

#Effect Arming Nuclear+Loading Bar
RED="\033[31m"
GRN="\033[32m"
YLW="\033[33m"
CYN="\033[36m"
RST="\033[0m"
spinner=["|","/","-","\\"]
bar_len=90
total_steps=110

print(GRN+"⚠ ARMING NUCLEAR PAYLOAD... ⚠\n")

for i in range(total_steps+1):
    filled=int(i/total_steps*bar_len)
    bar="█"*filled+"-"*(bar_len-filled)
    spin=spinner[i%len(spinner)]
    color=GRN if i<70 else YLW if i<90 else RED
    sys.stdout.write(f"\r{color}[{bar}]{i:3d}% {spin}{RST}")
    sys.stdout.flush()
    if i %17==0:
        winsound.Beep(1200,100)
    time.sleep(0.06)

print(GRN+"\n\n☢︎ ⚠ LAUNCH SEQUENCE INITIATED ⚠ ☢︎")
time.sleep(1)

for t in range(15,0,-1):
    sys.stdout.write(YLW+f"\r💣 T-{t}..."+RST)
    sys.stdout.flush()
    winsound.Beep(800, 300)
    time.sleep(0.5)

print(RED+"\n\nYES RICKO, KABOOM!\n")
winsound.Beep(2000,1500)
print(nuke(64))

'''
#Loading Systemnya
total = 5  #total untuk si detik countdown

for t in range(total,0,-1):
    bar_len=80
    filled=int((total-t+1)/total*bar_len)
    bar="█"*filled+"-"*(bar_len-filled)

    sys.stdout.write(f"\r[{bar}]{t}detik lagi...")
    sys.stdout.flush()
    time.sleep(1)

print("\nAwas ada sule!!!")
time.sleep(1.4)
print("\nprikitiw...!")
time.sleep(0.3)
print(nuke(10))
''' #model awal