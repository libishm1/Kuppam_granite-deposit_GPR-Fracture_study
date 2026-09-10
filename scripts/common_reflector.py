import sys, os, glob, csv
sys.path.insert(0, os.path.dirname(__file__))
import segy, numpy as np
from scipy.signal import hilbert
ROOT = r'D:/code_ws/reference/parsans/report/raw/GPR Raw data_Kuppam'
DTH, DTL = 0.0610352, 0.1220703
def agc_env(d, dt, w_ns=3.0):
    e = np.abs(hilbert(d, axis=1))
    w = max(3, int(w_ns/dt)); k = np.ones(w)/w
    sm = np.apply_along_axis(lambda r: np.convolve(r, k, 'same'), 1, e)
    return e/(sm+1e-12)
rows=[]
for blk in ['A Block','B Block','C Block']:
    for fh in sorted(glob.glob(os.path.join(ROOT, blk, '**', '*_HF.sgy'), recursive=True)):
        fl = fh[:-7]+'_LF.sgy'
        if not os.path.exists(fl): continue
        H = agc_env(segy.read(fh)['data'], DTH).mean(axis=0)
        L = agc_env(segy.read(fl)['data'], DTL).mean(axis=0)
        th = np.arange(len(H))*DTH; tl = np.arange(len(L))*DTL
        tg = np.arange(0, 30, DTH)
        A = np.interp(tg, th, H); B = np.interp(tg, tl, L)
        for name,(a0,a1) in [('surface 0-3ns',(0.0,3.0)), ('shallow 4-10ns',(4.0,10.0)), ('mid 8-16ns',(8.0,16.0))]:
            m=(tg>=a0)&(tg<a1); a=A[m]; b=B[m]
            if a.std()<1e-9 or b.std()<1e-9: continue
            a=(a-a.mean())/a.std(); b=(b-b.mean())/b.std()
            cc=np.correlate(b,a,'full'); lg=np.arange(-len(a)+1,len(a))*DTH
            k=np.abs(lg)<5.0; j=int(np.argmax(cc[k])); lag=lg[k][j]; r=cc[k][j]/len(a)
            i0=np.where(k)[0][j]
            if 0<i0<len(cc)-1:
                y0,y1,y2=cc[i0-1],cc[i0],cc[i0+1]; den=y0-2*y1+y2
                if den!=0: lag += DTH*0.5*(y0-y2)/den
            rows.append(dict(block=blk[0], line=os.path.basename(os.path.dirname(fh))[:34],
                             window=name, lag_ns=round(float(lag),4), r=round(float(r),4)))
w=csv.DictWriter(open('tables/common_reflector_lag.csv','w',newline='',encoding='utf-8'),
                 fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
import statistics as st
print('Lag of the LF record behind the HF record, envelope AGC, per time window')
print('(a common physical reflector must arrive at the same corrected time in both channels)\n')
print('%-16s %5s %9s %9s %9s %8s'%('window','n(r>.5)','median','mean','sd','mean r'))
for name in ['surface 0-3ns','shallow 4-10ns','mid 8-16ns']:
    s=[x for x in rows if x['window']==name and x['r']>0.5]
    al=[x for x in rows if x['window']==name]
    if not s: print('%-16s   none above r=0.5 (mean r %.2f)'%(name, st.mean([x['r'] for x in al]))); continue
    v=[x['lag_ns'] for x in s]
    print('%-16s %5d %9.3f %9.3f %9.3f %8.2f'%(name,len(s),st.median(v),st.mean(v),st.pstdev(v),
                                               st.mean([x['r'] for x in s])))
geo=(0.244-0.070)/0.299792458
print('\ngeometric part from the antenna offsets alone: %.3f ns'%geo)
for name in ['surface 0-3ns','shallow 4-10ns','mid 8-16ns']:
    s=[x['lag_ns'] for x in rows if x['window']==name and x['r']>0.5]
    if len(s)<20: continue
    m=st.median(s)
    print('  %-16s residual time-zero difference %.3f ns -> %.1f cm at v=0.118'%(name, m-geo,(m-geo)*0.118/2*100))
