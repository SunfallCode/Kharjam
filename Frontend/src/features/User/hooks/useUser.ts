import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as controller from "../helpers/controller";
import * as api from "../helpers/api";
import { useTranslations } from "next-intl";
import { useRef, useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { createProfileSchema, ProfileFormData } from "../interfaces/schema";
import { zodResolver } from "@hookform/resolvers/zod";
import { notify } from "@/components/ui/sonner";

export const useUser = () => {
  const t = useTranslations();
  const fileInputRef = useRef<any>(null);
  const queryClient = useQueryClient();

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
      card_holder_name: getProfileData?.card_holder_name ?? "",
      card_number: getProfileData?.card_number ?? "",
    },
  });

  const { mutate: updateProfileMutate, isPending: updateProfileIsPending } =
    useMutation(
      controller.UpdateProfileApiController({
        name: watch("name"),
        email: watch("email"),
        phone_number: watch("phone_number"),
        avatar: watch("avatar"),
        card_holder_name: watch("card_holder_name"),
        card_number: watch("card_number"),
      })
    );

  const { mutate: updateCardMutate, isPending: updateCardIsPending } = useMutation({
    mutationFn: async (data: { cardHolderName: string; cardNumber: string }) => {
      // Create FormData for card update only
      const formData = new FormData();
      formData.append('card_holder_name', data.cardHolderName);
      formData.append('card_number', data.cardNumber);

      return api.getUserService().updateProfileApi(formData);
    },
    onSuccess: (res: any) => {
      notify.success(res.data.message);
      queryClient.invalidateQueries({
        queryKey: ["getProfileDataApi"]
      });
    },
    onError: (error: any) => {
      notify.error(error.message);
    }
  });

  const handleCardUpdate = (cardHolderName: string, cardNumber: string, onSuccess?: () => void) => {
    updateCardMutate(
      { cardHolderName, cardNumber },
      {
        onSuccess: () => {
          if (onSuccess) onSuccess();
        }
      }
    );
  };

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
    handleCardUpdate,
  };
};
