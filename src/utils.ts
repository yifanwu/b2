export const STRICT = true;

export const FgRed = "\x1b[31m";
const FgGreen = "\x1b[32m";
const FgBlue = "\x1b[34m";
const FgMegenta = "\x1b[35m";
const FgGray = "\x1b[90m";
export const Reset = "\x1b[0m";

export function LogInternalError(message: string): null {
  console.log(`${FgRed}${message}${Reset}`);
  if (STRICT) {
    debugger;
    throw new Error(message);
  }
  return null;
}

export function LogSteps(func: string, message?: string) {
  console.log(`${FgGreen}[${func}] ${message}${Reset}`);
}

export function LogDebug(message: string) {
  console.log(`${FgMegenta}${message}${Reset}`);
}

export function hashCode(str: string) {
  let hash = 0, i, chr;
  if (str.length === 0) return hash;
  for (i = 0; i < str.length; i++) {
    chr   = str.charCodeAt(i);
    hash  = ((hash << 5) - hash) + chr;
    hash |= 0; // Convert to 32bit integer
  }
  return hash;
}