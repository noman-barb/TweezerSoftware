module.exports = {
    apps: [
      {
        name: 'locate_serivce',
        script: 'TrackingService1.py',
        cwd: 'Z:/backend/TrackService/',
        exec_mode: 'fork',
        args: '--n_procs 12'
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
        name: 'objective_heater_service',
        script: 'HeatService.py',
        cwd: 'Z:/backend/HeaterService/',
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
      // {
      //   name: 'locate_relay',
      //   script: 'RelayService.py',
      //   cwd: 'Z:/backend/TrackService/',
      //   post_start: async () => {
      //     await new Promise(resolve => setTimeout(resolve, 20000)); // Delay for 20 seconds
      //   }
      // },

      // {
      //   name: 'SLM_SERVICE',
      //   script: 'SLMService.py',
      //   cwd: 'Z:/backend/SLMService/',
      //   post_start: async () => {
      //     await new Promise(resolve => setTimeout(resolve, 2000)); // Delay for 20 seconds
      //   }
      // },

    ]
  };
  