import { render, screen } from '@testing-library/angular';
import { CountChartComponent, niceCeil } from './count-chart.component';
import { duration } from '../../pages/stats/stats.page';

describe('niceCeil', () => {
  it('rounds up to 1, 2 or 5 times a power of ten', () => {
    expect(niceCeil(1)).toBe(1);
    expect(niceCeil(13)).toBe(20);
    expect(niceCeil(41)).toBe(50);
    expect(niceCeil(120)).toBe(200);
  });
});

describe('duration', () => {
  it('shows days and hours, or hours and minutes', () => {
    expect(duration(177_323)).toBe('2 d 1 h');
    expect(duration(3_900)).toBe('1 h 5 min');
    expect(duration(59)).toBe('0 min');
  });
});

describe('CountChartComponent', () => {
  it('gives each bucket a tooltip with both directions', async () => {
    await render(CountChartComponent, {
      inputs: {
        series: {
          granularity: 'day',
          entered: 7,
          left: 5,
          buckets: [
            { start: '2026-10-29T00:00:00+01:00', entered: 3, left: 2 },
            { start: '2026-10-30T00:00:00+01:00', entered: 4, left: 3 },
          ],
        },
      },
    });
    expect(screen.getByRole('img', { name: 'Persons over time: 7 in, 5 out.' })).toBeTruthy();
    const titles = Array.from(document.querySelectorAll('title')).map((t) => t.textContent);
    expect(titles.some((t) => t?.endsWith(': 4 in, 3 out'))).toBe(true);
  });
});
