module.exports = {
    apps: [
      {
        name: 'locate_serivce',
        script: 'TrackingService1.py',
        cwd: 'Z:/backend/TrackService/',
        exec_mode: 'fork',
        args: '--n_procs 20'
      },
      {
        name: 'locate_relay',
        script: 'RelayService.py',
        cwd: 'Z:/backend/TrackService/',
      },

      {
        name: 'cam_service_1',
        script: 'CamService.py',
        cwd: 'Z:/backend/CamService/',
        args: '--port 4001'
      },
      {
        name: 'cam_service_2',
        script: 'CamService.py',
        cwd: 'Z:/backend/CamService/',
        args: '--port 4002'

      },
      {
        name: 'cam_relay_1',
        script: 'CamRelay1.py',
        cwd: 'Z:/backend/CamService/',
      },
      {
        name: 'cam_relay_2',
        script: 'CamRelay2.py',
        cwd: 'Z:/backend/CamService/',
      },
      {
        name: 'objective_heater_service',
        script: 'HeatService.py',
        cwd: 'Z:/backend/HeaterService/',
      }
    ]
  };
  