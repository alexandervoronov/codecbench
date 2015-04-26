'''
Created on Jun 11, 2014

@author: alberto
'''

import subprocess
import os
import re
import time

def x265_handler(run):
    """ does a run. returns metric info 
    returns:
    size of the encoded bitstream
    metric info SSIM/PSNR
    
    produces reconstructed yuv. provides size info 
    """
    
    root = os.path.dirname( __file__ ) + os.sep + run['platform'] + os.sep
    
    pars = {'codec':"x265",
            'width': run['seq']['width'],
            'height': run['seq']['height'],
            'num' : run['seq']['fpsnum'],
            'den' : run['seq']['fpsden'],
            'bitrate' : run['config']['bitrate'],
            'preset' : run['config'].get('preset', 'slow'),
            'passes' : run['config'].get('passes', 1),
            'muxedoutput' : run['output'] +".mp4",
            'output' : run['output']+".265",
            'fp_stats' : run['output']+".264" + '.fpstats',
            'input' : run['seq']['abspath'],
            'encoder' : os.path.abspath(root + "x265"),
            'decoder' : run['tools']['h265refdec'],
            'muxer' : run['tools']['mp4box'],
            'reconfile' : run['recon'],
            'vm' : run['tools']['vm'],
            'frame_count' : run['frame_count'],
            'platform' : run['platform']
    }
    
    
    
    try:
        
        clines = []
        
        command_p1 = ''
        command_p2 = ''
        if (pars['passes'] == 1):
            command_p1 = "{encoder} --fps={num}/{den} --bitrate={bitrate} --input-res {width}x{height} --preset {preset} -o {output} --frames {frame_count} {input}".format(**pars).split()
            clines.append(command_p1)
        else:
            command_p1 = "{encoder} --fps={num}/{den} --bitrate={bitrate} --pass=1 --stats={fp_stats} --input-res {width}x{height} --preset {preset} -o {output} --frames {frame_count} {input}".format(**pars).split()
            command_p2 = "{encoder} --fps={num}/{den} --bitrate={bitrate} --pass=2 --stats={fp_stats} --input-res {width}x{height} --preset {preset} -o {output} --frames {frame_count} {input}".format(**pars).split()
            clines.append(command_p1)
            clines.append(command_p2)
        
        # do encode
        startenc = time.time()
        out = subprocess.check_output(command_p1,stderr=subprocess.STDOUT).decode("utf-8")
        if (pars['passes'] > 1):
            p2_out = subprocess.check_output(command_p2,stderr=subprocess.STDOUT).decode("utf-8")
            out += p2_out
        stopenc = time.time()
        
        #filesize
        filesize = os.path.getsize(pars['output'])
        
        # #create muxed output for convenience
        # command = "{muxer} -add {output} {muxedoutput}".format(**pars).split()
        # out = subprocess.check_output(command,stderr=subprocess.STDOUT).decode("utf-8")
        
        framecount = run['seq']['frame_count']
        fps = pars['num']/pars['den']
        (totalbytes, bitsperframe, bps) = (filesize, filesize/framecount, (filesize*8)/(framecount/fps) )
        
        
        #do decode
        command = "{decoder}  -b {output}  -o {reconfile}".format(**pars).split();
        clines.append(command)
        out = subprocess.check_output(command)
        

        run['results'] = {'totalbytes': int(totalbytes), 'bitsperframe': int(bitsperframe), 'bps':int(bps), 'encodetime_in_s': (stopenc-startenc), 'clines': clines}
        
        
        #do video metrics
        metrics = run['tools']['do_video_metrics'](clines, **pars)
        run['results'].update(metrics)
        
        #delete recon if needed
        os.remove(run['recon']) if not run['keeprecon'] else None
            
        
    except subprocess.CalledProcessError as e:
        print(e)
        pass
    
    
codec = {
    "nickname": "x265",
    "profile": "x265",
    "out_extension": "265",
    "handler" : x265_handler,
    "supported_pars" : {"bitrate":1000,"preset":"fast",'passes':1},
    "ratesweep_pars" : ['bitrate']
}

def init(gconf):
    """ returns codec struct """
    # figure out versions
    exe = os.path.dirname( __file__ ) + os.sep + gconf['platform'] + os.sep + 'x265'
    try:
        out = subprocess.check_output([exe , "--version"], stderr=subprocess.STDOUT)
        version =  out.splitlines()[0].decode()
        version_long = out.decode()
    except:
        version = "?"
        version_long = "??"
        
    codec['version'] = version
    codec['version_long'] = version_long
    
    return codec
    
