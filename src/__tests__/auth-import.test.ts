import { AuthService } from '../lib/auth';

describe('Auth import test', () => {
  it('should import AuthService', () => {
    expect(AuthService).toBeDefined();
    expect(typeof AuthService.login).toBe('function');
  });
});