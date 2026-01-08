import { z } from "zod";

export const createProfileSchema = (t: (key: string) => string) => z.object({
  name: z.string().min(2, { message: t('profileNameMinShema') }).max(100, { message: t('profileNameMaxShema') }),
  phone_number: z.string()
    .min(1, t('profilePhoneRequired'))
    .regex(/^(\+98|0)?9\d{9}$/, t('profilePhoneInvalid')),
  email: z.string().regex(/^[^\s@]+@[^\s@]+\.[^\s@]+$/, t('profileEmailSchema')).optional().or(z.literal("")),
  avatar: z.instanceof(File).optional(),
  card_holder_name: z.string().optional(),
  card_number: z.string().optional(),
});

export type ProfileFormData = z.infer<ReturnType<typeof createProfileSchema>>;