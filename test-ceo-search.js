fetch('https://adoptai.codecrafter.fr/speakers?search=CEO')
  .then(r => r.json())
  .then(d => {
    console.log('Total CEO results:', d.count);
    const damien = d.speakers.find(s => s.name === 'Damien Gromier');
    console.log('Damien Gromier found:', !!damien);
    if (damien) {
      console.log('Damien:', JSON.stringify(damien, null, 2));
    } else {
      console.log('First 3 speakers:');
      d.speakers.slice(0, 3).forEach(s =>
        console.log(s.name, '-', s.title, '@', s.company)
      );
    }
  });
