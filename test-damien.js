fetch('https://adoptai.codecrafter.fr/speakers')
  .then(r => r.json())
  .then(d => {
    const damien = d.speakers.find(s => s.name === 'Damien Gromier');
    console.log('Damien Gromier:', JSON.stringify(damien, null, 2));
  });
