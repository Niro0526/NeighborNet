import { createTheme, MantineColorsTuple } from '@mantine/core';

// Custom emerald color shades based on #16866A
const emeraldColor: MantineColorsTuple = [
  '#E6F7F2',
  '#C0EAE0',
  '#96DDCB',
  '#65CFB5',
  '#34C19E',
  '#16866A', // Primary (index 5)
  '#0F735B',
  '#09664F', // Primary Dark (index 7)
  '#064C3B',
  '#043327',
];

export const theme = createTheme({
  primaryColor: 'emerald',
  colors: {
    emerald: emeraldColor,
  },
  fontFamily: 'Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  defaultRadius: 'md',
  cursorType: 'pointer',
});
