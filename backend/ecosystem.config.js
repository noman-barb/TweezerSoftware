module.exports = {
    apps: [
      {
        name: 'Tracking Service',
        script: 'TrackingService1.py',
        cwd: 'Z:/backend/TrackService/',
        exec_mode: 'fork',
        args: '--n_procs 20'
      },
      {
        name: 'Camera Service 1',
        script: 'CamService.py',
        cwd: 'Z:/backend/CamService/',
        args: '--port 4001'

      },
      {
        name: 'Camera Service 2',
        script: 'CamService.py',
        cwd: 'Z:/backend/CamService/',
        args: '--port 4002'

      }
    ]
  };
  