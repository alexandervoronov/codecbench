'''
Created on Jun 11, 2014

@author: alberto
'''

import subprocess
import os
import re
import time
import copy

def libvpx_handler(run):
    """ does a run. returns metric info 
    returns:
    size of the encoded bitstream
    metric info SSIM/PSNR
    
    produces reconstructed yuv. provides size info 
    """
    
    root = os.path.dirname( __file__ ) + os.sep + run['platform'] + os.sep
    
    pars = {'codec': run['config'].get('libvpx_codec', "vp9"),
            'width': run['seq']['width'],
            'height': run['seq']['height'],
            'num' : run['seq']['fpsnum'],
            'den' : run['seq']['fpsden'],
            'bitrate' : run['config']['bitrate'],
            'output' : run['output'] + '.ivf',
            'fp_stats' : run['output'] + '.ivf' + '.fpf',
            'cpu' : run['config'].get('cpu', 16),
            'passes' : run['config'].get('passes', 1),
            'input' : run['seq']['abspath'],
            'encoder' : os.path.abspath(root + "vpxenc"),
            'decoder' : os.path.abspath(root + "vpxdec"),
            'reconfile' : run['recon'],
            'vm' : run['tools']['vm'],
            'frame_count' : run['frame_count'],
            'tune_setting' : ''
    }
    
    if run['config'].get('tune', None):
        pars['tune_setting'] = '--tune={}'.format(run['config']['tune'])

    try:
        
        clines = []
        command = "{encoder} --cpu-used={cpu} --passes={passes} --pass=1 --fpf={fp_stats} --fps={num}/{den} --target-bitrate={bitrate} --codec={codec} -w {width} -h {height} -o {output} --limit={frame_count} {tune_setting} {input}".format(**pars).split()
        command_p1 = command
        command_p2 = copy.deepcopy(command_p1)
        command_p2[command_p2.index('--pass=1')] = '--pass=2'
        clines.append(command_p1)
        # do encode
        startenc = time.time()
        out = subprocess.check_output(command_p1,stderr=subprocess.STDOUT).decode("utf-8")
        if pars['passes'] > 1:
            clines.append(command_p2)
            p2_out = subprocess.check_output(command_p2,stderr=subprocess.STDOUT).decode("utf-8")
        stopenc = time.time()
        
        # filesize
        filesize = os.path.getsize(pars['output'])
        framecount = run['seq']['frame_count']
        fps = pars['num']/pars['den']
        (totalbytes, bitsperframe, bps) = (filesize, filesize/framecount, (filesize*8)/(framecount/fps) )
        
        #do decode
        command = "{decoder}  {output} --rawvideo  -o {reconfile}".format(**pars).split();
        clines.append(command)
        out = subprocess.check_output(command)
        
        run['results'] = {'totalbytes': int(totalbytes), 'bitsperframe': int(bitsperframe), 'bps':int(bps), 'encodetime_in_s': (stopenc-startenc), 'clines': clines}
        
        
        #do video metrics
        metrics = run['tools']['do_video_metrics'](clines, **pars)
        run['results'].update(metrics)
        
        #delete recon if needed
        os.remove(run['recon']) if not run['keeprecon'] else None
        
        
    except subprocess.CalledProcessError as e:
        print (e.output)
        pass
    
    
codec = {
    "nickname": "libvpx",
    "profile": "libvpx",
    "out_extension": "ivf",
    "handler" : libvpx_handler,
    "supported_pars" : {'bitrate':1000,'cpu':16,'libvpx_codec':'vp9', 'passes':1, 'tune':None},
    "ratesweep_pars" : ['bitrate']
}


def init(gconf):
    """ returns codec struct """
    # figure out versions
    exe = os.path.dirname( __file__ ) + os.sep + gconf['platform'] + os.sep + 'vpxenc'
    try:
         
        p = subprocess.Popen( [exe], stderr=subprocess.PIPE, stdout=subprocess.PIPE )
        out, err = p.communicate()
        err = err.decode().replace('\r\n','\n')
        
        search = re.compile("vp8.+(v\d+\..*)$", re.MULTILINE).search(err)
        vp8ver,  = search.groups()
        
        search = re.compile("vp9.+(v\d+\..*)$", re.MULTILINE).search(err)
        vp9ver, = search.groups()
        
        version = "vp8: {0}, vp9: {1}".format(vp8ver, vp9ver)
        version_long = version
    except Exception as e:
        version = "?"
        version_long = "??"
        
    codec['version'] = version
    codec['version_long'] = version_long
    
    return codec
    

    