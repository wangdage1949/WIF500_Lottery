<img width="1280" height="720" alt="image" src="https://github.com/user-attachments/assets/a0f31683-1f8d-43fe-802a-6d78f9de6ac7" />
wif500
Address: 1PfNh5fRcE9JKDmicD2Rh3pexGwce1LqyU 500 BTC
Known part of the 40/52 compressed wif key: ....5bCRZhiS5sEGMpmcRZdpAhmWLRfMmutGmPHtjVob
GOOD luck

命令如下：
WifSolverCuda.exe -wif LXXXXXXXXXXX5bCRZhiS5sEGMpmcRZdpAhmWLRfMmutGmPHtjVob -a 1PfNh5fRcE9JKDmicD2Rh3pexGwce1LqyU -n 41 -n2 51 -multi -gpu-list 0,1,2,3,4,5 -s 8000 -turbo 12

以6*3070TI为例，预计25年可以跑完

<img width="1128" height="486" alt="image" src="https://github.com/user-attachments/assets/3b684441-85a1-4419-9f19-1b6bbbc068e6" />

以100*4090为例，预计 12 天可以跑完。

1.2cpu版本已发布  https://github.com/wangdage1949/WIF500_Lottery/releases/tag/v1.2

详细模式（显示所有信息）：
btc_lottery.exe  --method 9 --count 10000000000000000 --batch-size 10000 --verbose

快速模式（只显示统计）：
btc_lottery.exe --method 1 --count 10000000000000000 --batch-size 1000 --fast

普通模式（平衡显示）
btc_lottery.exe --method 1 --count 100000000000000000 --batch-size 1000
