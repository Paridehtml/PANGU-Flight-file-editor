typedef unsigned long long UINT_PTR;
typedef UINT_PTR SOCKET;

void pan_protocol_safety_checks(void);
void pan_protocol_start(SOCKET);
void pan_protocol_finish(SOCKET);
unsigned char *pan_protocol_get_image(SOCKET, unsigned long *);
void pan_protocol_set_viewpoint_by_angle(SOCKET, float, float, float, float, float, float);
void pan_protocol_set_viewpoint_by_quaternion_s(SOCKET s, float x, float y, float z, float q0, float q1, float q2, float q3);
void pan_protocol_set_field_of_view(SOCKET s, float f);
unsigned char *pan_protocol_get_viewpoint_by_degrees_d(SOCKET, double, double, double, double, double, double, unsigned long *);
unsigned char *pan_protocol_get_viewpoint_by_quaternion_s(SOCKET, float, float, float, float, float, float, float, unsigned long *);