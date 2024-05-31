module.exports = {
    apps: [
      {
        name: 'Track Service',
        script: 'TrackService.py',
        cwd: 'Z:/backend/TrackService/'
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
  