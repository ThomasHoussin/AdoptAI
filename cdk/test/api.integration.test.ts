import { describe, it, expect } from 'vitest';

const API_BASE_URL = 'https://adoptai.codecrafter.fr';

describe('AdoptAI API Integration Tests', () => {
  describe('GET /', () => {
    it('should return llms.txt documentation', async () => {
      const response = await fetch(`${API_BASE_URL}/`);

      expect(response.status).toBe(200);
      expect(response.headers.get('content-type')).toContain('text/plain');
      expect(response.headers.get('content-type')).toContain('charset=utf-8');
      expect(response.headers.get('access-control-allow-origin')).toBe('*');

      const text = await response.text();
      expect(text).toContain('Adopt AI Grand Palais 2025');
      expect(text).toContain('240+ sessions');
      expect(text).toContain('•'); // Test UTF-8 encoding
    });
  });

  describe('GET /llms.txt', () => {
    it('should return same content as /', async () => {
      const [rootResponse, llmsResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/`),
        fetch(`${API_BASE_URL}/llms.txt`),
      ]);

      expect(rootResponse.status).toBe(200);
      expect(llmsResponse.status).toBe(200);

      const rootText = await rootResponse.text();
      const llmsText = await llmsResponse.text();

      expect(rootText).toBe(llmsText);
    });
  });

  describe('GET /robots.txt', () => {
    it('should return robots.txt', async () => {
      const response = await fetch(`${API_BASE_URL}/robots.txt`);

      expect(response.status).toBe(200);
      expect(response.headers.get('content-type')).toContain('text/plain');

      const text = await response.text();
      expect(text).toContain('User-agent: *');
      expect(text).toContain('Allow: /');
    });
  });

  describe('GET /health', () => {
    it('should return healthy status', async () => {
      const response = await fetch(`${API_BASE_URL}/health`);

      expect(response.status).toBe(200);
      expect(response.headers.get('content-type')).toContain('application/json');
      expect(response.headers.get('content-type')).toContain('charset=utf-8');

      const data = await response.json() as any;
      expect(data).toEqual({
        status: 'healthy',
        service: 'adoptai-api',
      });
    });
  });

  describe('GET /sessions', () => {
    it('should return all sessions without filters', async () => {
      const response = await fetch(`${API_BASE_URL}/sessions`);

      expect(response.status).toBe(200);
      expect(response.headers.get('content-type')).toContain('application/json');
      expect(response.headers.get('access-control-allow-origin')).toBe('*');

      const data = await response.json() as any;
      expect(data).toHaveProperty('total');
      expect(data).toHaveProperty('count');
      expect(data).toHaveProperty('sessions');
      expect(data.total).toBe(243);
      expect(data.count).toBe(243);
      expect(Array.isArray(data.sessions)).toBe(true);

      const session = data.sessions[0];
      expect(session).toHaveProperty('id');
      expect(session).toHaveProperty('title');
      expect(session).toHaveProperty('date');
      expect(session).toHaveProperty('time');
      expect(session).toHaveProperty('stage');
      expect(session).toHaveProperty('speakers');
      expect(session).toHaveProperty('ecosystems');
    });

    it('should filter by date (2025-11-25)', async () => {
      const response = await fetch(`${API_BASE_URL}/sessions?date=2025-11-25`);
      const data = await response.json() as any;

      expect(response.status).toBe(200);
      expect(data.count).toBe(133); // Exact count from metadata
      expect(data.filters).toHaveProperty('date', '2025-11-25');

      // All sessions must be on Nov 25
      data.sessions.forEach((session: any) => {
        expect(session.date).toContain('Nov 25');
      });

      // Verify specific known sessions are present
      const ceoIntro = data.sessions.find((s: any) =>
        s.title === 'CEO STAGE - INTRODUCTORY REMARKS'
      );
      expect(ceoIntro).toBeDefined();
      expect(ceoIntro.time).toContain('9:00 AM');
      expect(ceoIntro.stage).toBe('CEO Stage');
      expect(ceoIntro.speakers[0].name).toBe('Damien Gromier');

      const nobelSession = data.sessions.find((s: any) =>
        s.title.includes('PHILIPPE AGHION') && s.title.includes('NOBEL')
      );
      expect(nobelSession).toBeDefined();
      expect(nobelSession.time).toContain('9:30 AM');
      expect(nobelSession.speakers[0].name).toBe('Philippe Aghion');
    });

    it('should filter by date (2025-11-26)', async () => {
      const response = await fetch(`${API_BASE_URL}/sessions?date=2025-11-26`);
      const data = await response.json() as any;

      expect(response.status).toBe(200);
      expect(data.count).toBe(110); // Exact count from metadata
      expect(data.filters).toHaveProperty('date', '2025-11-26');

      // All sessions must be on Nov 26
      data.sessions.forEach((session: any) => {
        expect(session.date).toContain('Nov 26');
      });

      // Verify specific known session
      const visionaryKeynote = data.sessions.find((s: any) =>
        s.title.includes('VISIONNARY KEYNOTE') && s.title.includes('NICOLAS NAMIAS')
      );
      expect(visionaryKeynote).toBeDefined();
      expect(visionaryKeynote.time).toContain('9:15 AM');
      expect(visionaryKeynote.stage).toBe('CEO Stage');
      expect(visionaryKeynote.speakers[0].name).toBe('Nicolas Namias');
    });

    it('should filter by stage', async () => {
      const response = await fetch(`${API_BASE_URL}/sessions?stage=CEO%20Stage`);
      const data = await response.json() as any;

      expect(response.status).toBe(200);
      expect(data.count).toBeGreaterThan(0);
      expect(data.filters).toHaveProperty('stage', 'CEO Stage');

      // All sessions must be on CEO Stage
      data.sessions.forEach((session: any) => {
        expect(session.stage.toLowerCase()).toContain('ceo stage');
      });

      // Verify specific CEO Stage sessions are present
      const nobelSession = data.sessions.find((s: any) =>
        s.title.includes('PHILIPPE AGHION') && s.title.includes('NOBEL')
      );
      expect(nobelSession).toBeDefined();
      expect(nobelSession.date).toBe('Nov 25, 2025');

      const ceoIntro = data.sessions.find((s: any) =>
        s.title === 'CEO STAGE - INTRODUCTORY REMARKS'
      );
      expect(ceoIntro).toBeDefined();
      expect(ceoIntro.speakers[0].name).toBe('Damien Gromier');
    });

    it('should filter by time (morning)', async () => {
      const response = await fetch(`${API_BASE_URL}/sessions?time=morning`);
      const data = await response.json() as any;

      expect(response.status).toBe(200);
      expect(data.count).toBeGreaterThan(0);
      expect(data.filters).toHaveProperty('time', 'morning');

      // Verify morning sessions are included (before 12:00 PM)
      const morningSession = data.sessions.find((s: any) => s.time?.startsWith('9:00 AM'));
      expect(morningSession).toBeDefined();

      // Verify no afternoon sessions (12:00 PM or later)
      const afternoonSession = data.sessions.find((s: any) =>
        s.time?.startsWith('12:') && s.time?.includes('PM') ||
        s.time?.startsWith('1:') && s.time?.includes('PM') ||
        s.time?.startsWith('2:') && s.time?.includes('PM')
      );
      expect(afternoonSession).toBeUndefined();
    });

    it('should filter by time (afternoon)', async () => {
      const response = await fetch(`${API_BASE_URL}/sessions?time=afternoon`);
      const data = await response.json() as any;

      expect(response.status).toBe(200);
      expect(data.count).toBeGreaterThan(0);
      expect(data.filters).toHaveProperty('time', 'afternoon');

      // Verify afternoon sessions are included (12:00 PM or later)
      const afternoonSession = data.sessions.find((s: any) =>
        s.time?.startsWith('12:00 PM')
      );
      expect(afternoonSession).toBeDefined();

      // Verify no morning sessions (before 12:00 PM)
      const morningSession = data.sessions.find((s: any) =>
        s.time?.startsWith('9:') && s.time?.includes('AM') ||
        s.time?.startsWith('10:') && s.time?.includes('AM') ||
        s.time?.startsWith('11:') && s.time?.includes('AM')
      );
      expect(morningSession).toBeUndefined();
    });

    it('should search by text', async () => {
      const response = await fetch(`${API_BASE_URL}/sessions?search=AI`);
      const data = await response.json() as any;

      expect(response.status).toBe(200);
      expect(data.count).toBeGreaterThan(0);
      expect(data.filters).toHaveProperty('search', 'AI');

      // Verify ALL results contain the search term (case-insensitive)
      // Search should match: title, speaker name, speaker company, or speaker title
      data.sessions.forEach((session: any) => {
        const searchTerm = 'ai';
        const titleMatch = session.title?.toLowerCase().includes(searchTerm);
        const speakerMatch = session.speakers?.some((sp: any) =>
          sp.name?.toLowerCase().includes(searchTerm) ||
          sp.company?.toLowerCase().includes(searchTerm) ||
          sp.title?.toLowerCase().includes(searchTerm)
        );
        const ecosystemMatch = session.ecosystems?.some((eco: any) =>
          eco?.toLowerCase().includes(searchTerm)
        );

        expect(titleMatch || speakerMatch || ecosystemMatch).toBe(true);
      });

      // Verify specific known session is present
      const adoptAISession = data.sessions.find((s: any) =>
        s.title.includes('ADOPT AI')
      );
      expect(adoptAISession).toBeDefined();
    });

    it('should search for Nobel and find specific session', async () => {
      const response = await fetch(`${API_BASE_URL}/sessions?search=Nobel`);
      const data = await response.json() as any;

      expect(response.status).toBe(200);
      expect(data.count).toBeGreaterThan(0);

      // Verify Philippe Aghion Nobel session is in results
      const nobelSession = data.sessions.find((s: any) =>
        s.title.includes('PHILIPPE AGHION') && s.title.includes('NOBEL')
      );
      expect(nobelSession).toBeDefined();
      expect(nobelSession.speakers[0].name).toBe('Philippe Aghion');
      expect(nobelSession.speakers[0].company).toContain('Nobel');
    });

    it('should search for banking and find specific session', async () => {
      const response = await fetch(`${API_BASE_URL}/sessions?search=banking`);
      const data = await response.json() as any;

      expect(response.status).toBe(200);
      expect(data.count).toBeGreaterThan(0);

      // Verify banking session is in results
      const bankingSession = data.sessions.find((s: any) =>
        s.title === 'Building The Next Generation of Banking with AI'
      );
      expect(bankingSession).toBeDefined();
      expect(bankingSession.speakers.some((sp: any) => sp.name === 'Yves Tyrode')).toBe(true);
      expect(bankingSession.speakers.some((sp: any) => sp.name === 'Lubomira Rochet')).toBe(true);
    });

    it('should combine multiple filters', async () => {
      const response = await fetch(`${API_BASE_URL}/sessions?date=2025-11-25&time=morning`);
      const data = await response.json() as any;

      expect(response.status).toBe(200);
      expect(data.filters).toHaveProperty('date', '2025-11-25');
      expect(data.filters).toHaveProperty('time', 'morning');

      // All sessions must be on Nov 25 AND in the morning
      data.sessions.forEach((session: any) => {
        expect(session.date).toContain('Nov 25');
        // Morning is before 12:00 PM (time field starts with AM or starts with 12:xx AM)
        expect(session.time).toMatch(/(AM|11:[0-9]{2} AM)/);
      });

      // Verify specific morning session on Nov 25 is present
      const ceoIntro = data.sessions.find((s: any) =>
        s.title === 'CEO STAGE - INTRODUCTORY REMARKS'
      );
      expect(ceoIntro).toBeDefined();
      expect(ceoIntro.date).toBe('Nov 25, 2025');
      expect(ceoIntro.time).toContain('9:00 AM');
    });

    it('should combine date and stage filters', async () => {
      const response = await fetch(`${API_BASE_URL}/sessions?date=2025-11-25&stage=CEO%20Stage`);
      const data = await response.json() as any;

      expect(response.status).toBe(200);
      expect(data.filters).toHaveProperty('date', '2025-11-25');
      expect(data.filters).toHaveProperty('stage', 'CEO Stage');

      // All sessions must be Nov 25 AND CEO Stage
      data.sessions.forEach((session: any) => {
        expect(session.date).toContain('Nov 25');
        expect(session.stage).toBe('CEO Stage');
      });

      // Verify specific sessions are present
      const ceoIntro = data.sessions.find((s: any) =>
        s.title === 'CEO STAGE - INTRODUCTORY REMARKS'
      );
      expect(ceoIntro).toBeDefined();

      const nobelSession = data.sessions.find((s: any) =>
        s.title.includes('PHILIPPE AGHION')
      );
      expect(nobelSession).toBeDefined();
    });

    it('should handle now parameter', async () => {
      const response = await fetch(`${API_BASE_URL}/sessions?now=true`);
      const data = await response.json() as any;

      expect(response.status).toBe(200);
      expect(data).toHaveProperty('currentTime');
      expect(data).toHaveProperty('ongoing');
      expect(data).toHaveProperty('upcoming');
      expect(data.ongoing).toHaveProperty('count');
      expect(data.ongoing).toHaveProperty('sessions');
      expect(data.upcoming).toHaveProperty('count');
      expect(data.upcoming).toHaveProperty('description', 'Sessions starting within 30 minutes');
      expect(data.upcoming).toHaveProperty('sessions');

      // Verify ongoing and upcoming counts match array lengths
      expect(data.ongoing.count).toBe(data.ongoing.sessions.length);
      expect(data.upcoming.count).toBe(data.upcoming.sessions.length);

      // If there are ongoing sessions, verify they have required fields
      if (data.ongoing.count > 0) {
        data.ongoing.sessions.forEach((session: any) => {
          expect(session).toHaveProperty('title');
          expect(session).toHaveProperty('time');
          expect(session).toHaveProperty('stage');
        });
      }

      // If there are upcoming sessions, verify they have required fields
      if (data.upcoming.count > 0) {
        data.upcoming.sessions.forEach((session: any) => {
          expect(session).toHaveProperty('title');
          expect(session).toHaveProperty('time');
          expect(session).toHaveProperty('stage');
        });
      }

      // Note: Can't verify specific sessions since this test runs at different times
      // The actual time-based logic is tested in Python unit tests with mocked time
    });

    it('should return empty results for non-existent filter', async () => {
      const response = await fetch(`${API_BASE_URL}/sessions?stage=NonExistentStage`);
      const data = await response.json() as any;

      expect(response.status).toBe(200);
      expect(data.count).toBe(0);
      expect(data.sessions).toHaveLength(0);
    });
  });

  describe('GET /speakers', () => {
    it('should return all speakers without filters', async () => {
      const response = await fetch(`${API_BASE_URL}/speakers`);

      expect(response.status).toBe(200);
      expect(response.headers.get('content-type')).toContain('application/json');
      expect(response.headers.get('access-control-allow-origin')).toBe('*');

      const data = await response.json() as any;
      expect(data).toHaveProperty('count');
      expect(data).toHaveProperty('speakers');
      expect(data.count).toBe(499);
      expect(Array.isArray(data.speakers)).toBe(true);

      const speaker = data.speakers[0];
      expect(speaker).toHaveProperty('name');

      // Verify some known speakers are present
      const damienGromier = data.speakers.find((s: any) => s.name === 'Damien Gromier');
      expect(damienGromier).toBeDefined();
      expect(damienGromier.company).toBe('Artefact');

      const philippeAghion = data.speakers.find((s: any) => s.name === 'Philippe Aghion');
      expect(philippeAghion).toBeDefined();
      expect(philippeAghion.company).toContain('Nobel');
    });

    it('should search speakers by text', async () => {
      const response = await fetch(`${API_BASE_URL}/speakers?search=CEO`);
      const data = await response.json() as any;

      expect(response.status).toBe(200);
      expect(data.count).toBeGreaterThan(0);
      expect(Array.isArray(data.speakers)).toBe(true);

      // Verify ALL results contain "CEO" (case-insensitive) in name, title, or company
      data.speakers.forEach((speaker: any) => {
        const searchTerm = 'ceo';
        const nameMatch = speaker.name?.toLowerCase().includes(searchTerm);
        const titleMatch = speaker.title?.toLowerCase().includes(searchTerm);
        const companyMatch = speaker.company?.toLowerCase().includes(searchTerm);

        expect(nameMatch || titleMatch || companyMatch).toBe(true);
      });

      // Verify Damien Gromier (CEO & Founder) is in results
      const damienGromier = data.speakers.find((s: any) => s.name === 'Damien Gromier');
      expect(damienGromier).toBeDefined();
      expect(damienGromier.title.toLowerCase()).toContain('ceo');
    });

    it('should search speakers by name', async () => {
      const response = await fetch(`${API_BASE_URL}/speakers?search=Aghion`);
      const data = await response.json() as any;

      expect(response.status).toBe(200);
      expect(data.count).toBeGreaterThan(0);

      // Verify Philippe Aghion is in results
      const aghion = data.speakers.find((s: any) => s.name === 'Philippe Aghion');
      expect(aghion).toBeDefined();
      expect(aghion.company).toContain('Nobel');
    });
  });

  describe('404 Error', () => {
    it('should return 404 for unknown path', async () => {
      const response = await fetch(`${API_BASE_URL}/invalid-path`);

      expect(response.status).toBe(404);
      expect(response.headers.get('content-type')).toContain('application/json');

      const data = await response.json() as any;
      expect(data).toHaveProperty('error', 'Not Found');
      expect(data).toHaveProperty('message');
      expect(data).toHaveProperty('available_endpoints');
      expect(data.available_endpoints).toContain('/sessions');
    });
  });

  describe('CORS and OPTIONS', () => {
    it('should handle OPTIONS request', async () => {
      const response = await fetch(`${API_BASE_URL}/sessions`, { method: 'OPTIONS' });

      expect(response.status).toBe(200);
      expect(response.headers.get('access-control-allow-origin')).toBe('*');
      expect(response.headers.get('access-control-allow-methods')).toContain('GET');
    });
  });
});
