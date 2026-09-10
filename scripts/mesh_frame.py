"""Bounding box, PCA and top-plane estimate for each photogrammetry mesh. Streams vertices only."""
import numpy as np, sys, os, time
def load_v(path, stride=1, maxn=None):
    out=[]; k=0
    with open(path,'rb') as f:
        for ln in f:
            if ln[:2]!=b'v ': continue
            k+=1
            if k%stride: continue
            p=ln.split(); out.append((float(p[1]),float(p[2]),float(p[3])))
            if maxn and len(out)>=maxn: break
    return np.array(out)
def ransac_plane(P, n_it=300, thr=0.03, rng=np.random.default_rng(0)):
    best=(0,None)
    for _ in range(n_it):
        i=rng.choice(len(P),3,replace=False); a,b,c=P[i]
        n=np.cross(b-a,c-a); nn=np.linalg.norm(n)
        if nn<1e-9: continue
        n/=nn; d=np.abs((P-a)@n); cnt=(d<thr).sum()
        if cnt>best[0]: best=(cnt,(n,a))
    n,a=best[1]; inl=np.abs((P-a)@n)<thr
    # refine on inliers
    Q=P[inl]; c=Q.mean(0); u,s,vt=np.linalg.svd(Q-c,full_matrices=False); n=vt[2]
    return n,c,inl.mean(),Q
for f,stride in (('block a.obj',8),('block b.obj',4),('block_c_decimated_1M.obj',4)):
    t=time.time(); P=load_v(f,stride)
    c=P.mean(0); u,s,vt=np.linalg.svd(P-c,full_matrices=False)
    ext=(P-c)@vt.T; span=ext.max(0)-ext.min(0)
    print('=== %s  %d verts (stride %d, %.0fs) ==='%(f,len(P),stride,time.time()-t))
    print('  bbox min %s max %s'%(np.round(P.min(0),2),np.round(P.max(0),2)))
    print('  PCA spans along principal axes: %.2f x %.2f x %.2f (units as stored)'%tuple(span))
    print('  PCA axis 1 %s  axis 3 (thinnest) %s'%(np.round(vt[0],3),np.round(vt[2],3)))
    n,pc,frac,Q=ransac_plane(P[::max(1,len(P)//60000)])
    # in-plane extent of the dominant plane's inliers
    e1=np.cross(n,[1,0,0]); e1/=np.linalg.norm(e1); e2=np.cross(n,e1)
    uv=np.c_[(Q-pc)@e1,(Q-pc)@e2]; cc=uv.mean(0); U,S,VT=np.linalg.svd(uv-cc,full_matrices=False); q=(uv-cc)@VT.T
    print('  dominant plane: normal %s, %.0f%% of points within 3 cm, in-plane extent %.2f x %.2f'%(np.round(n,3),100*frac,*(q.max(0)-q.min(0))))
    # residual scatter of ALL points from this plane, signed
    d=(P-pc)@n
    print('  signed distance of all points to that plane: 5th %.2f  50th %.2f  95th %.2f  (block height shows as the tail)'%tuple(np.percentile(d,[5,50,95])))
