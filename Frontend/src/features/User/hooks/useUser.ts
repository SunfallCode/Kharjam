import { useMutation, useQuery } from "@tanstack/react-query";
import * as controller from "../helpers/controller";
import { useTranslations } from "next-intl";
import { useRef, useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { createProfileSchema, ProfileFormData } from "../interfaces/schema";
import { zodResolver } from "@hookform/resolvers/zod";

export const useUser = () => {
  const t = useTranslations();
  const fileInputRef = useRef<any>(null);

  const [preview, setPreview] = useState("/character.png");

  const { data: getProfileData, isPending: getProfileDataIsPending } = useQuery(
    controller.GetProfileApiController()
  );

  useEffect(() => {
    if (getProfileData?.avatar_url) {
      setPreview(getProfileData.avatar_url)
    }
  }, [getProfileData?.avatar_url]);

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleImage = (e: any) => {
    const file = e.target.files[0];
    if (!file) return;
    const url = URL.createObjectURL(file);
    setPreview(url);
    setValue("avatar", file, { shouldValidate: true });
  };

  const {
    watch,
    setValue,
    getValues,
    handleSubmit,
    formState: { errors },
  } = useForm<ProfileFormData>({
    resolver: zodResolver(createProfileSchema(t)),
    mode: "all",
    values: {
      name: getProfileData?.name ?? "",
      email: getProfileData?.email ?? "",
      phone_number: getProfileData?.phone_number ?? "",
    },
  });

  const { mutate: updateProfileMutate, isPending: updateProfileIsPending } =
    useMutation(
      controller.UpdateProfileApiController({
        name: watch("name"),
        email: watch("email"),
        phone_number: watch("phone_number"),
        avatar: watch("avatar"),
      })
    );

  return {
    t,
    watch,
    errors,
    preview,
    setValue,
    getValues,
    handleClick,
    handleImage,
    handleSubmit,
    fileInputRef,
    getProfileData,
    updateProfileMutate,
    updateProfileIsPending,
    getProfileDataIsPending,
  };
};
