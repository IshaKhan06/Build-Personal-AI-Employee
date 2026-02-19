module.exports = {
  apps: [
    {
      name: 'facebook_instagram_watcher',
      script: 'python',
      args: 'watchers/facebook_instagram_watcher.py facebook',
      cwd: __dirname,
      interpreter: 'none',
      watch: false,
      max_restarts: 5,
      min_uptime: '10s',
      restart_delay: 4000,
      autorestart: true,
      restart_on_exit: false,
      env: {
        'PYTHONUNBUFFERED': '1',
        'PYTHONUTF8': '1',
        'PYTHONIOENCODING': 'utf-8'
      },
      error_file: './Logs/pm2_facebook_watcher_err.log',
      out_file: './Logs/pm2_facebook_watcher_out.log',
      log_file: './Logs/pm2_facebook_watcher_combined.log',
      time: true,
      merge_logs: true,
      kill_timeout: 3000
    },
    {
      name: 'instagram_watcher',
      script: 'python',
      args: 'watchers/facebook_instagram_watcher.py instagram',
      cwd: __dirname,
      interpreter: 'none',
      watch: false,
      max_restarts: 5,
      min_uptime: '10s',
      restart_delay: 4000,
      autorestart: true,
      restart_on_exit: false,
      env: {
        'PYTHONUNBUFFERED': '1',
        'PYTHONUTF8': '1',
        'PYTHONIOENCODING': 'utf-8'
      },
      error_file: './Logs/pm2_instagram_watcher_err.log',
      out_file: './Logs/pm2_instagram_watcher_out.log',
      log_file: './Logs/pm2_instagram_watcher_combined.log',
      time: true,
      merge_logs: true,
      kill_timeout: 3000
    },
    {
      name: 'twitter_watcher',
      script: 'python',
      args: 'watchers/twitter_watcher.py',
      cwd: __dirname,
      interpreter: 'none',
      watch: false,
      max_restarts: 5,
      min_uptime: '10s',
      restart_delay: 4000,
      autorestart: true,
      restart_on_exit: false,
      env: {
        'PYTHONUNBUFFERED': '1',
        'PYTHONUTF8': '1',
        'PYTHONIOENCODING': 'utf-8'
      },
      error_file: './Logs/pm2_twitter_watcher_err.log',
      out_file: './Logs/pm2_twitter_watcher_out.log',
      log_file: './Logs/pm2_twitter_watcher_combined.log',
      time: true,
      merge_logs: true,
      kill_timeout: 3000
    },
    {
      name: 'social_summary_generator',
      script: 'python',
      args: 'skills/social_summary_generator/social_summary_generator.py',
      cwd: __dirname,
      interpreter: 'none',
      watch: false,
      max_restarts: 3,
      min_uptime: '5s',
      restart_delay: 2000,
      autorestart: false,
      env: {
        'PYTHONUNBUFFERED': '1',
        'PYTHONUTF8': '1',
        'PYTHONIOENCODING': 'utf-8'
      },
      error_file: './Logs/pm2_social_summary_err.log',
      out_file: './Logs/pm2_social_summary_out.log',
      log_file: './Logs/pm2_social_summary_combined.log',
      time: true,
      merge_logs: true,
      kill_timeout: 3000
    },
    {
      name: 'twitter_post_generator',
      script: 'python',
      args: 'skills/twitter_post_generator/twitter_post_generator.py',
      cwd: __dirname,
      interpreter: 'none',
      watch: false,
      max_restarts: 3,
      min_uptime: '5s',
      restart_delay: 2000,
      autorestart: false,
      env: {
        'PYTHONUNBUFFERED': '1',
        'PYTHONUTF8': '1',
        'PYTHONIOENCODING': 'utf-8'
      },
      error_file: './Logs/pm2_twitter_post_generator_err.log',
      out_file: './Logs/pm2_twitter_post_generator_out.log',
      log_file: './Logs/pm2_twitter_post_generator_combined.log',
      time: true,
      merge_logs: true,
      kill_timeout: 3000
    },
    {
      name: 'weekly_audit_briefer',
      script: 'python',
      args: 'skills/weekly_audit_briefer/weekly_audit_briefer.py',
      cwd: __dirname,
      interpreter: 'none',
      watch: false,
      max_restarts: 3,
      min_uptime: '5s',
      restart_delay: 2000,
      autorestart: false,
      env: {
        'PYTHONUNBUFFERED': '1',
        'PYTHONUTF8': '1',
        'PYTHONIOENCODING': 'utf-8'
      },
      error_file: './Logs/pm2_weekly_audit_briefer_err.log',
      out_file: './Logs/pm2_weekly_audit_briefer_out.log',
      log_file: './Logs/pm2_weekly_audit_briefer_combined.log',
      time: true,
      merge_logs: true,
      kill_timeout: 3000
    }
  ]
};
