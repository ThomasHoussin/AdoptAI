const fs = require('fs');
const data = JSON.parse(fs.readFileSync('data/sessions.json', 'utf8'));

function parseTime(t) {
  if (!t) return 0;
  const [time, period] = t.split(' ');
  const [h, m] = time.split(':').map(Number);
  let hour = h;
  if (period === 'PM' && hour !== 12) hour += 12;
  if (period === 'AM' && hour === 12) hour = 0;
  return hour * 60 + (m || 0);
}

const nov25 = data.sessions.filter(s => s.date === 'Nov 25, 2025');
const currentTime = parseTime('12:49 PM');

const ongoing = nov25.filter(s => {
  const start = parseTime(s.startTime);
  const end = parseTime(s.endTime);
  return start <= currentTime && currentTime < end;
});

const upcoming = nov25.filter(s => {
  const start = parseTime(s.startTime);
  return start > currentTime && start <= currentTime + 30;
});

console.log('At 12:50 PM Nov 25:');
console.log('\nONGOING (' + ongoing.length + '):');
ongoing.forEach(s => console.log('- ' + s.startTime + '-' + s.endTime + ': ' + s.title));

console.log('\nUPCOMING (' + upcoming.length + '):');
upcoming.forEach(s => console.log('- ' + s.startTime + '-' + s.endTime + ': ' + s.title));
