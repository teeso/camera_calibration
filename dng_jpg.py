import numpy as np
from sys import argv
from matplotlib import pyplot as plt
from ispex import plot, io
from ispex.raw import pull_apart
from ispex.general import Rsquare
from ispex.gamma import malus, malus_error
from glob import glob

folder_main = argv[1]

subfolders = glob(folder_main+"/*")
subfolders = [s for s in subfolders if "." not in s]

pols = np.zeros_like(subfolders, dtype=np.uint16)
saturated = np.zeros_like(subfolders, dtype=np.uint32)

Ms = np.zeros_like(subfolders, dtype=np.float32)
Merrs = Ms.copy()

jMs = np.tile(0, (len(subfolders), 3)).astype(np.float32)
jMerrs = jMs.copy()

meanarrs = []
jpgmeanarrs = []
#vararrs = []
#jpgvararrs = []

for i,folder in enumerate(subfolders):
    pols[i] = folder.split("pol")[-1]

    arrs, colors = io.load_dng_many(folder+"/*.dng", return_colors=True)

    mean = arrs.mean(axis=0).astype(np.float32)  # mean per x,y
    meanarrs.append(mean)
#    vararrs.append(arrs.var(axis=0))

    means = arrs.mean(axis=(1,2))
    mean_all = means.mean()
    mean_err = means.std() / np.sqrt(len(means) - 1)

    saturated[i] = len(np.where(arrs == 4095)[0])

    Ms[i], Merrs[i] = mean_all, mean_err

    JPGs = glob(folder+"/*.jpg")
    jpgarrs = [plt.imread(jpg) for jpg in JPGs]
    jpgarrs = np.stack(jpgarrs)
    jpgmean = jpgarrs.mean(axis=0).astype(np.float32) # mean per x,y,C
    jpgmeanarrs.append(jpgmean)
#    jpgvararrs.append(jpgarrs.var(axis=0))

    jpgmeans = jpgarrs.mean(axis=(1,2))
    jpgmean_all = jpgmeans.mean(axis=0)
    jpgmean_err = jpgmeans.std(axis=0) / np.sqrt(len(jpgmeans) - 1)

    jMs[i], jMerrs[i] = jpgmean_all, jpgmean_err

    print(f"{(i+1)/len(subfolders)*100:.0f}%", end=" ")
print("")

meanarrs = np.stack(meanarrs)
#vararrs = np.stack(vararrs)
jpgmeanarrs = np.stack(jpgmeanarrs)
#jpgvararrs = np.stack(jpgvararrs)

M_RGBG, _ = pull_apart(meanarrs.T, colors) ; M_RGBG = M_RGBG.T
print("Split DNG means")
J_RGBG, _ = pull_apart(np.moveaxis(jpgmeanarrs, 0, 2), colors)
J_RGBG = np.moveaxis(J_RGBG, 0, 3)
J_RGBG = np.moveaxis(J_RGBG, 2, 0)
print("Split JPEG means")
#V_RGBG, _ = pull_apart(vararrs.T , colors) ; V_RGBG = V_RGBG.T

Is = malus(pols)
Ierrs = malus_error(pols, sigma_angle0=1.0)

m1, m2 = M_RGBG.shape[1]//2, M_RGBG.shape[2]//2
fig, axs = plt.subplots(2, 2, tight_layout=True, figsize=(10,5), sharex=True, sharey=True)
for j in range(4):
    i = j if j < 3 else 1
    c = "rgb"[i]
    ax = axs.ravel()[j]
    ax.errorbar(Is, J_RGBG[:,m1,m2,j,i], xerr=Ierrs, fmt=f"{c}o")
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(0, 255*1.05)

    ax2 = ax.twinx()
    ax2.errorbar(Is, M_RGBG[:,m1,m2,j], xerr=Ierrs, fmt="ko")
    ax2.set_ylim(0, 4095*1.05)
    if j%2:
        ax2.set_ylabel("DNG value")
    else:
        ax.set_ylabel("JPEG value")
        ax2.tick_params(axis="y", labelright=False)
    if j//2:
        ax.set_xlabel("Intensity")
fig.savefig("results/linearity/RGBG.png")
plt.close()
print("RGBG JPG-DNG comparison made")

plt.figure(figsize=(8,5), tight_layout=True)
plt.hexbin(M_RGBG[::3,...,1], J_RGBG[::3,...,1,1], mincnt=1, cmap=plot.cmaps["Gr"])
plt.xlabel("DNG value")
plt.ylabel("JPEG value")
plt.title("DNG-JPEG relation under different lighting conditions")
plt.savefig("results/linearity/G_dng_jpeg.png")
plt.close()

def linear_R2(Is, row, saturate=4000):
    ind = np.where(row < 4000)
    p = np.polyfit(Is[ind], row[ind], 1)
    pv = np.polyval(p, Is[ind])
    R2 = Rsquare(row[ind], pv)
    return R2

print("R^2 comparison...", end=" ")
M_reshaped = M_RGBG.reshape(len(M_RGBG), -1, 4)
M_reshaped = np.ma.array(M_reshaped, mask=M_reshaped>4000)
R2 = np.zeros((4, len(M_reshaped[0])))
for j in range(4):
    R2[j] = [linear_R2(Is, row, saturate=4000) for row in M_reshaped[...,j].T]
    print(j, end=" ")

fig, axs = plt.subplots(2, 2, sharex=True, sharey=True, tight_layout=True, figsize=(7,7))
for j in range(4):
    ax = axs.ravel()[j]
    c = "rgbg"[j]
    ax.hist(R2[j], bins=np.linspace(0.995,1,200), color=c)
for ax in axs[1]:
    ax.set_xlabel("$R^2$")
for ax in axs[:,0]:
    ax.set_ylabel("Frequency")
fig.savefig("results/linearity/R2.png")
plt.close()
print("made")