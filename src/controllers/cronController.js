const moment = require('moment-timezone');
const User = require('../models/User');
const { getTasksClient } = require('../services/google');
const { sendMessage } = require('../services/telegram');

exports.runTaskChecks = async (req, res) => {
  console.log('Cron hit: Starting checks...');
  
  try {
    const users = await User.find({ googleRefreshToken: { $exists: true } });

    for (const user of users) {
      await checkUserTasks(user);
    }

    res.status(200).send('Checks completed');
  } catch (error) {
    console.error('Cron error:', error);
    res.status(500).send('Error running checks');
  }
};

async function checkUserTasks(user) {
  try {
    const tasksService = getTasksClient(user.googleRefreshToken);
    
    // Get all task lists
    const { data: taskLists } = await tasksService.tasklists.list();
    if (!taskLists.items) return;

    for (const list of taskLists.items) {
      // Get tasks for this list
      const { data: tasks } = await tasksService.tasks.list({
        tasklist: list.id,
        showCompleted: false,
        showHidden: false,
      });

      if (!tasks.items) continue;

      for (const task of tasks.items) {
        if (!task.due) continue;
        analyzeTask(user, task);
      }
    }
  } catch (error) {
    console.error(`Error checking tasks for user ${user.telegramChatId}:`, error.message);
  }
}

function analyzeTask(user, task) {
  // task.due comes in RFC 3339 format
  const now = moment().tz(user.timezone);
  const taskDue = moment(task.due).tz(user.timezone);
  
  // Google Tasks "Date Only" tasks (no specific time) default to T00:00:00.000Z
  const isDateOnly = task.due.includes('00:00:00.000Z'); 

  // Logic 1: 9 PM check for tasks due tomorrow (No Time Attached)
  if (isDateOnly) {
    if (now.hour() === 21) {
      const tomorrow = moment().tz(user.timezone).add(1, 'days').startOf('day');
      if (taskDue.isSame(tomorrow, 'day')) {
        sendMessage(user.telegramChatId, `📅 Reminder: You have "${task.title}" due tomorrow. Start working!`);
      }
    }
  } 
  
  // Logic 2 & 3: tasks with specific time
  else {
    const diffInHours = taskDue.diff(now, 'hours', true);
    
    // Check 6 Hours
    if (diffInHours >= 5.5 && diffInHours < 6.5) {
       sendMessage(user.telegramChatId, ` Heads up: You have "${task.title}" due in 6 hours.`);
    }

    // Check 1 Hour
    if (diffInHours >= 0.5 && diffInHours < 1.5) {
       sendMessage(user.telegramChatId, ` Urgent: You have "${task.title}" due in 1 hour. Get ready!`);
    }
  }
}