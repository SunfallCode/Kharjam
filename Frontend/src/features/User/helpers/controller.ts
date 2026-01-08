import { queryOptions, useMutation, useQueryClient } from "@tanstack/react-query";
import * as api from "./api";
import { UserUpdate } from "./api.schemas";
import { notify } from "@/components/ui/sonner";
const { getProfileApi, updateProfileApi } = api.getUserService();

export const GetProfileApiController = () =>
  queryOptions({
    queryKey: ["getProfileDataApi"],
    queryFn: async () => {
      return getProfileApi().then((res: any) => {
        return res.data;
      });
    },
  });

  export const UpdateProfileApiController = (
    body: UserUpdate & { avatar?: File }
 ) => {
    const queryClient = useQueryClient();
    return {
       mutationKey: ["updateProfileDataApi"],
       mutationFn: () => {
         // Create FormData for file upload
         const formData = new FormData();

        // Add text fields
        if (body.name !== undefined && body.name !== null) formData.append('name', body.name);
        if (body.email !== undefined && body.email !== null) formData.append('email', body.email);
        if (body.phone_number !== undefined && body.phone_number !== null) formData.append('phone_number', body.phone_number);
        if (body.card_holder_name !== undefined && body.card_holder_name !== null) formData.append('card_holder_name', body.card_holder_name);
        if (body.card_number !== undefined && body.card_number !== null) formData.append('card_number', body.card_number);

         // Add file if exists
         if (body.avatar) {
           formData.append('profile_image', body.avatar);
         }

         return updateProfileApi(formData);
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
    };
 };
