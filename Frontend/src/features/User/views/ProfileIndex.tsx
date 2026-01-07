import { Input } from "@/components/ui/input";
import { useUser } from "../hooks/useUser";
import { Button } from "@/components/ui/button";
import { CreditCardIcon } from "@/assets/icons/CreditCardIcon";
import { ImageIcon } from "@/assets/icons/ImageIcon";
import {
  DrawerComponent,
} from "@/components/ui/drawer";
import { CreditCardManagement } from "@/components/CreditCardManagement";
import { useState } from "react";

const ProfileIndex = () => {
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const {
    t,
    watch,
    errors,
    preview,
    setValue,
    handleClick,
    handleImage,
    handleSubmit,
    fileInputRef,
    updateProfileMutate,
    updateProfileIsPending,
  } = useUser();

  return (
    <div className="w-full flex flex-col items-center justify-center">
      <div
        className="relative flex items-center justify-center cursor-pointer"
        onClick={handleClick}
      >
        <div className="w-40 h-40 rounded-full border-4 border-sky-200 flex items-center justify-center bg-inherit overflow-hidden">
          <img
            src={preview}
            alt="avatar"
            className="size-full object-contain"
          />
        </div>

        <div className="absolute right-0 top-3/4 -translate-y-1/2 bg-sky-400 shadow-md rounded-full p-1">
          <ImageIcon className="w-4 h-4 stroke-gray-100" />
        </div>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleImage}
          className="hidden"
        />
      </div>
      <p className="mt-4 text-3xl text-text-base font-bold">
        {t("profile-header")}
      </p>
      <p className="mt-1 mb-4 text-text-secondary text-sm font-medium">
        {t("profile-subHeader")}
      </p>
      <div className="w-11/12">
        <Input
          value={watch("name")}
          placeholder={t("profile-fullname-placeholder")}
          onChange={(e) =>
            setValue("name", e.target.value, {
              shouldValidate: true,
            })
          }
        />
        {errors.name && (
          <p className="text-red-500 text-sm mt-1">{errors.name.message}</p>
        )}
      </div>
      <div className="w-11/12 my-4">
        <Input
          value={watch("phone_number")}
          placeholder={t("profile-phone-placeholder")}
          onChange={(e) =>
            setValue("phone_number", e.target.value, {
              shouldValidate: true,
            })
          }
          addonAfter={
            <div className="text-xs bg-sky-300 px-2 py-1 rounded-md cursor-pointer text-gray-100">
              {t("verify")}
            </div>
          }
        />
        {errors.phone_number && (
          <p className="text-red-500 text-sm mt-1">
            {errors.phone_number.message}
          </p>
        )}
      </div>
      <div className="w-11/12">
        <Input
          value={watch("email")}
          onChange={(e) =>
            setValue("email", e.target.value, {
              shouldValidate: true,
            })
          }
          placeholder={t("profile-email-placeholder")}
          addonAfter={
            <div className="text-xs bg-sky-300 px-2 py-1 rounded-md cursor-pointer text-gray-100">
              {t("verify")}
            </div>
          }
        />
        {errors.email && (
          <p className="text-red-500 text-sm mt-1">{errors.email.message}</p>
        )}
      </div>
      <Button
        onClick={() => {
          handleSubmit(() => {
            updateProfileMutate();
          })();
        }}
        disabled={updateProfileIsPending}
        type="submit"
        size="lg"
        className="w-2/3 mt-6"
      >
        {t("profile-submit-btn")}
      </Button>
      <Button
        onClick={() => setIsDrawerOpen(true)}
        size="lg"
        className="w-1/3 mt-6"
      >
        <CreditCardIcon />
        <span>{t("profile-cards-btn")}</span>
      </Button>
      <DrawerComponent
        description={t("drawer-credit-cards-description")}
        title={t("drawer-credit-cards-title")}
        open={isDrawerOpen}
        setOpen={setIsDrawerOpen}
        content={<CreditCardManagement />}
      />
    </div>
  );
};

export default ProfileIndex;
