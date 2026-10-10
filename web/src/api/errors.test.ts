import { ApiError, parseErrorType } from './api-error';
import { fieldPathToName, toUiError } from './errors';

const apiError = (type: string, status: number, body: Record<string, unknown>) =>
  new ApiError({ type, status, body });

describe('toUiError', () => {
  it('maps ValidationException fieldList onto form field names', () => {
    const err = apiError('ValidationException', 400, {
      message: 'invalid',
      fieldList: [
        { path: '/username', message: 'must not be empty' },
        { path: '/password', message: 'too short' },
        { path: '/password', message: 'ignored duplicate' },
      ],
    });
    expect(toUiError(err)).toEqual({
      kind: 'validation',
      message: 'invalid',
      fields: { username: 'must not be empty', password: 'too short' },
    });
  });

  it('flattens nested paths', () => {
    expect(fieldPathToName('/items/0/name')).toBe('items.0.name');
  });

  it('maps 401 to unauthorized even without a type header', () => {
    expect(toUiError(apiError('UnauthorizedError', 401, { message: 'nope' })).kind).toBe(
      'unauthorized',
    );
    expect(toUiError(new ApiError({ status: 401, body: { message: 'nope' } })).kind).toBe(
      'unauthorized',
    );
  });

  it('keeps request ids from server errors', () => {
    const err = apiError('InternalServerError', 500, { message: 'boom', requestId: 'r-1' });
    expect(toUiError(err)).toEqual({ kind: 'server', message: 'boom', requestId: 'r-1' });
  });

  it('exposes the newer uploader on guideline conflicts', () => {
    const err = apiError('GuidelinesConflictError', 409, {
      message: 'newer version exists',
      latestVersionId: 'v2',
      uploadedBy: { id: 'u2', username: 'agent2', displayName: 'Agent2' },
      uploadedAt: '2026-09-13T00:00:00Z',
    });
    expect(toUiError(err)).toMatchObject({
      kind: 'conflict',
      code: 'guidelines_conflict',
      uploadedBy: 'Agent2',
      latestVersionId: 'v2',
    });
  });

  it('distinguishes the three 409 errors by type', () => {
    expect(toUiError(apiError('ConflictError', 409, { message: 'dup' }))).toMatchObject({
      code: 'conflict',
    });
    expect(
      toUiError(apiError('GuidelinesNotReadyError', 409, { message: 'x', companyId: 'c' })),
    ).toMatchObject({
      code: 'guidelines_not_ready',
      companyId: 'c',
    });
  });

  it('classifies fetch failures as network errors', () => {
    expect(toUiError(new TypeError('Failed to fetch')).kind).toBe('network');
  });

  it('never throws on unknown input', () => {
    expect(toUiError('weird')).toEqual({ kind: 'unknown', message: 'weird' });
  });
});

describe('parseErrorType', () => {
  it('handles the header formats Smithy protocols use', () => {
    expect(parseErrorType('NotFoundError')).toBe('NotFoundError');
    expect(parseErrorType('assistant.api#NotFoundError')).toBe('NotFoundError');
    expect(parseErrorType('NotFoundError:http://internal.amazon.com/coral/x/')).toBe(
      'NotFoundError',
    );
    expect(parseErrorType(null)).toBeUndefined();
  });
});
