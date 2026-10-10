import type { components } from './schema';

export type Schemas = components['schemas'];

export type User = Schemas['User'];
export type Company = Schemas['Company'];
export type GuidelineStatus = Schemas['GuidelineStatus'];
export type GuidelineVersionSummary = Schemas['GuidelineVersionSummary'];
export type GuidelineChunk = Schemas['GuidelineChunk'];
export type Conversation = Schemas['Conversation'];
export type ConversationSummary = Schemas['ConversationSummary'];
export type Message = Schemas['Message'];
export type MessageKind = Schemas['MessageKind'];
export type MessageRole = Schemas['MessageRole'];
export type Coverage = Schemas['Coverage'];
export type AssistantGuidance = Schemas['AssistantGuidance'];
export type Correction = Schemas['Correction'];
export type FeedbackRating = Schemas['FeedbackRating'];
export type FeedbackSummary = Schemas['FeedbackSummary'];
export type RetrievedChunk = Schemas['RetrievedChunk'];
export type UsedCorrection = Schemas['UsedCorrection'];
